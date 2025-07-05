from rest_framework import permissions, viewsets
from rest_framework.decorators import action

from expenses.models import Expense
from expenses.serializers.expenses import ExpenseSerializer


class ExpenseViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        user = self.request.user
        return Expense.objects.select_related("category", "trip").filter(user=user)

    @action(detail=False, methods=["post"])
    def load_from_csv(self, request):
        import csv
        from django.db import transaction
        from expenses.models import ExpenseCategory, Trip
        from rest_framework.response import Response
        from rest_framework import status
        from io import TextIOWrapper

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
        with transaction.atomic():
            for i, row in enumerate(reader, 1):
                try:
                    # Categoria: cerca per code, crea se non esiste
                    cat_code = row["category"].strip()
                    category, _ = ExpenseCategory.objects.get_or_create(
                        user=user,
                        code=cat_code,
                        defaults={"name": cat_code, "for_expense": True},
                    )
                    # Trip: cerca per code, crea se non esiste
                    trip_code = row["trip"].strip()
                    trip = None
                    if trip_code:
                        trip, _ = Trip.objects.get_or_create(
                            user=user, code=trip_code, defaults={"name": trip_code}
                        )
                    # Tipologia: True per expense, False per income
                    is_expense = (
                        row.get("typology", "expense").strip().lower() != "income"
                    )
                    # Crea Expense
                    Expense.objects.create(
                        user=user,
                        expense_date=row["expense_date"],
                        description=row["description"],
                        forecast_amount=row["forecast_amount"],
                        actual_amount=row["actual_amount"],
                        amortization_start_date=row["amortization_start_date"],
                        amortization_end_date=row["amortization_end_date"],
                        category=category,
                        trip=trip,
                        is_expense=is_expense,
                    )
                    created += 1
                except Exception as e:
                    errors.append({"row": i, "error": str(e)})
        return Response(
            {"created": created, "errors": errors},
            status=status.HTTP_201_CREATED if created else status.HTTP_400_BAD_REQUEST,
        )
