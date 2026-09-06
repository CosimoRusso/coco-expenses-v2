import csv
import datetime as dt
import io
from dataclasses import asdict, dataclass
from io import TextIOWrapper

import django_filters
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from expenses.date_utils import from_italian_date, is_italian_date
from expenses.models import Currency, Expense, ExpenseCategory, Trip
from expenses.serializers.expenses import ExpenseSerializer
from expenses.utils.encryption.encryption import (
    decrypt_text_with_key,
    encrypt_text_with_key,
)
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class ExpenseFilterSet(django_filters.FilterSet):
    is_expense = django_filters.BooleanFilter()
    category = django_filters.NumberFilter()
    trip = django_filters.NumberFilter()

    def filter_queryset(self, queryset):
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        if start_date:
            try:
                start_date = dt.date.fromisoformat(start_date)
            except ValueError:
                raise serializers.ValidationError(
                    "Start date must be in YYYY-MM-DD format"
                )
        if end_date:
            try:
                end_date = dt.date.fromisoformat(end_date)
            except ValueError:
                raise serializers.ValidationError(
                    "End date must be in YYYY-MM-DD format"
                )
        if start_date or end_date:
            queryset = self.filter_by_date_range(queryset, start_date, end_date)

        queryset = super().filter_queryset(queryset)
        return queryset

    def filter_by_date_range(self, queryset, start_date, end_date):
        if start_date and end_date:
            return queryset.filter(
                (
                    Q(amortization_start_date__lte=start_date)
                    & Q(amortization_end_date__gte=start_date)
                )
                | (
                    Q(amortization_start_date__gte=start_date)
                    & Q(amortization_start_date__lte=end_date)
                )
            )
        elif start_date:
            return queryset.filter(
                (
                    Q(amortization_start_date__lte=start_date)
                    & Q(amortization_end_date__gte=start_date)
                )
                | (Q(amortization_start_date__gte=start_date))
            )
        elif end_date:
            return queryset.filter(amortization_start_date__lte=end_date)
        return queryset

    class Meta:
        model = Expense
        fields = ["is_expense", "category", "trip"]


class ExpenseViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ExpenseSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ExpenseFilterSet
    pagination_class = PageNumberPagination
    ordering_fields = [
        "expense_date",
        "amortization_start_date",
        "amortization_end_date",
    ]
    ordering = ["-expense_date"]

    def get_queryset(self):
        user = self.request.user
        return (
            Expense.objects.select_related("category", "trip")
            .filter(user=user)
            .order_by("-expense_date")
        )

    @action(detail=False, methods=["post"])
    def load_from_csv(self, request):
        user = request.user
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": "File non fornito"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Supporta file UTF-8
        csv_file = TextIOWrapper(file, encoding="utf-8")
        reader = csv.DictReader(csv_file)
        created = 0
        errors = []
        user_is_encrypted = user.usersettings.is_encrypted
        user_crypto_key = request.COOKIES.get("user_crypto_key")
        if user_is_encrypted and not user_crypto_key:
            raise ValidationError(
                "Encryption key not present in cookie 'user_crypto_key'"
            )
        with transaction.atomic():
            for i, row in enumerate(reader, 1):
                try:
                    is_expense = row.get("is_expense", "True").strip().lower() == "true"
                    # Categoria: cerca per code, crea se non esiste
                    cat_code = row["category"].strip()
                    category, _ = ExpenseCategory.objects.get_or_create(
                        user=user,
                        code=cat_code,
                        defaults={"name": cat_code, "for_expense": is_expense},
                    )
                    # Trip: cerca per code, crea se non esiste
                    trip_code = row["trip"].strip()
                    trip = None
                    if trip_code:
                        trip, _ = Trip.objects.get_or_create(
                            user=user, code=trip_code, defaults={"name": trip_code}
                        )

                    # Process date fields
                    for date_field in [
                        "expense_date",
                        "amortization_start_date",
                        "amortization_end_date",
                    ]:
                        if row.get(date_field):
                            row[date_field] = (
                                from_italian_date(row[date_field])
                                if is_italian_date(row[date_field])
                                else row[date_field]
                            )
                    if row.get("amount"):
                        row["amount"] = (
                            float(row["amount"].replace(",", ".").strip())
                            if isinstance(row["amount"], str)
                            else row["amount"]
                        )
                    if user_is_encrypted:
                        amount = None
                        encrypted_amount = encrypt_text_with_key(
                            user, user_crypto_key, str(row["amount"])
                        )
                        description = ""
                        encrypted_description = encrypt_text_with_key(
                            user, user_crypto_key, row["description"]
                        )
                    else:
                        amount = row["amount"]
                        encrypted_amount = ""
                        description = row["description"]
                        encrypted_description = ""
                    # Currency
                    currency = Currency.objects.get(code=row["currency"])
                    # Crea Expense
                    Expense.objects.create(
                        user=user,
                        expense_date=row["expense_date"],
                        description=description,
                        encrypted_description=encrypted_description,
                        amount=amount,
                        encrypted_amount=encrypted_amount,
                        amortization_start_date=row["amortization_start_date"],
                        amortization_end_date=row["amortization_end_date"],
                        category=category,
                        trip=trip,
                        currency=currency,
                        is_expense=is_expense,
                    )
                    created += 1
                except Exception as e:
                    errors.append({"row": i, "error": str(e)})
        return Response(
            {"created": created, "errors": errors},
            status=status.HTTP_201_CREATED if created else status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=False, methods=["get"])
    def download_csv(self, request):
        user = request.user
        queryset = Expense.objects.select_related(
            "trip", "category", "currency"
        ).order_by("expense_date", "id")

        buffer = io.StringIO()
        fieldnames = list(ExpenseCSV.__annotations__.keys())
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()

        data = []
        for expense in queryset.iterator():
            amount = expense.amount
            description = expense.description
            if user.usersettings.is_encrypted:
                crypto_key = request.COOKIES.get("user_crypto_key")
                amount = decrypt_text_with_key(
                    user, crypto_key, expense.encrypted_amount
                )
                description = decrypt_text_with_key(
                    user, crypto_key, expense.encrypted_description
                )
            data.append(
                asdict(
                    ExpenseCSV(
                        amount=amount,
                        description=description,
                        category=expense.category.code,
                        trip=expense.trip and expense.trip.code,
                        currency=expense.currency.code,
                        expense_date=expense.expense_date,
                        amortization_start_date=expense.amortization_start_date,
                        amortization_end_date=expense.amortization_end_date,
                        is_expense=expense.is_expense,
                    )
                )
            )

        writer.writerows(data)

        mem_file = io.BytesIO(buffer.getvalue().encode("utf-8"))

        response = FileResponse(
            mem_file,
            content_type="text/csv",
            as_attachment=True,
            filename="users_export.csv",
        )
        response["Access-Control-Expose-Headers"] = "Content-Disposition"
        return response


@dataclass
class ExpenseCSV:
    amount: str
    description: str
    category: str
    trip: str
    currency: str
    expense_date: str
    amortization_start_date: str
    amortization_end_date: str
    is_expense: bool
