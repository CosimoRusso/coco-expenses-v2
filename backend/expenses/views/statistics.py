from decimal import Decimal

from django.db.models import QuerySet
from expenses.date_utils import all_dates_in_range
from expenses.models import Currency, Expense, ExpenseCategory, Trip, UserSettings
from expenses.serializers.statistics import (
    AmortizationTimelineSerializer,
    CategoryStatisticsSerializer,
    StatisticsInputSerializer,
    TripStatisticsSerializer,
)
from expenses.statistics_utils import (
    convert_expenses_to_currency,
    convert_expenses_to_statistics_expenses,
    get_expenses_date_range_in_currency,
    get_non_expenses_date_range,
)
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet


class StatisticViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        Expense.objects.filter(user=user).select_related("category", "trip")

    @action(detail=False, methods=["GET"])
    def expense_categories(self, request, *args, **kwargs):
        user = self.request.user
        queryset: QuerySet[Expense] = Expense.objects.filter(user=user).select_related(
            "category", "trip"
        )
        categories = ExpenseCategory.objects.filter(user=request.user, for_expense=True)
        input_serializer = StatisticsInputSerializer(data=request.query_params)
        input_serializer.is_valid(raise_exception=True)
        start_date = input_serializer.validated_data["start_date"]
        end_date = input_serializer.validated_data["end_date"]
        currency: Currency = (
            input_serializer.validated_data.get("currency")
            or UserSettings.objects.get(user=user).preferred_currency
            or Currency.objects.get(code="USD")
        )
        all_expenses_in_currency = get_expenses_date_range_in_currency(
            queryset,
            currency=currency,
            start_date=start_date,
            end_date=end_date,
        )
        expenses = {
            day: [e for e in all_expenses_in_currency[day] if e.is_expense]
            for day in all_expenses_in_currency
        }
        result = {category: {"amount": 0} for category in categories}

        for category in categories:
            for day in all_dates_in_range(start_date, end_date):
                if day in expenses:
                    for expense in expenses[day]:
                        if expense.category == category:
                            result[category]["amount"] += expense.amount

        result = [
            {
                "category": category,
                "currency": currency,
                "amount": data["amount"],
            }
            for category, data in result.items()
        ]

        serializer = CategoryStatisticsSerializer(result, many=True)
        response = list(
            sorted(
                serializer.data, key=lambda item: float(item["amount"]), reverse=True
            )
        )
        return Response(response)

    @action(detail=False, methods=["GET"])
    def trips(self, request, *args, **kwargs):
        user = self.request.user
        queryset: QuerySet[Expense] = Expense.objects.filter(user=user).select_related(
            "category", "trip"
        )
        trips = Trip.objects.filter(user=request.user)
        input_serializer = StatisticsInputSerializer(data=request.query_params)
        input_serializer.is_valid(raise_exception=True)
        start_date = input_serializer.validated_data["start_date"]
        end_date = input_serializer.validated_data["end_date"]
        currency: Currency = (
            input_serializer.validated_data.get("currency")
            or UserSettings.objects.get(user=user).preferred_currency
            or Currency.objects.get(code="USD")
        )

        # Get original expenses (before amortization) that overlap with date range
        all_expenses = queryset.filter(is_expense=True)
        expenses_as_statistics = convert_expenses_to_statistics_expenses(all_expenses)
        expenses_in_currency = convert_expenses_to_currency(
            expenses_as_statistics, currency
        )

        # Filter expenses that overlap with the date range
        overlapping_expenses = []
        date_range_days = set(all_dates_in_range(start_date, end_date))
        for expense in expenses_in_currency:
            expense_days = set(
                all_dates_in_range(
                    expense.amortization_start_date, expense.amortization_end_date
                )
            )
            if expense_days & date_range_days:  # If there's any overlap
                overlapping_expenses.append(expense)

        # Initialize result with all trips and None for expenses without a trip
        trip_amounts = {trip: {"amount": Decimal("0.00")} for trip in trips}
        trip_amounts[None] = {"amount": Decimal("0.00")}

        # Calculate average daily amount based on amortization period from start_date onwards
        for expense in overlapping_expenses:
            trip = expense.trip
            if expense.amortization_start_date and expense.amortization_end_date:
                # Calculate effective amortization period: from max(start_date, amortization_start_date) to amortization_end_date
                effective_start = max(start_date, expense.amortization_start_date)
                effective_end = expense.amortization_end_date
                if effective_start <= effective_end:
                    num_days = (effective_end - effective_start).days + 1
                    if num_days > 0:
                        daily_amount = expense.amount / num_days
                        trip_amounts[trip]["amount"] += daily_amount

        result = []
        for trip, data in trip_amounts.items():
            if data["amount"] > 0:  # Only include trips with expenses
                # Handle None trips by creating a dict representation
                if trip is None:
                    trip_data = {
                        "id": None,
                        "code": "",
                        "name": "No Trip",
                        "is_active": False,
                    }
                else:
                    # Use TripSerializer to serialize the trip instance
                    from expenses.serializers.trips import TripSerializer

                    trip_serializer = TripSerializer(trip)
                    trip_data = trip_serializer.data
                result.append(
                    {
                        "trip": trip_data,
                        "currency": currency,
                        "amount": data["amount"],
                    }
                )

        serializer = TripStatisticsSerializer(result, many=True)
        response = list(
            sorted(
                serializer.data, key=lambda item: float(item["amount"]), reverse=True
            )
        )
        return Response(response)

    @action(detail=False, methods=["GET"])
    def amortization_timeline(self, request, *args, **kwargs):
        user = self.request.user
        queryset: QuerySet[Expense] = Expense.objects.filter(user=user).select_related(
            "category", "trip"
        )
        input_serializer = StatisticsInputSerializer(data=request.query_params)
        input_serializer.is_valid(raise_exception=True)
        start_date = input_serializer.validated_data["start_date"]
        end_date = input_serializer.validated_data["end_date"]
        currency: Currency = (
            input_serializer.validated_data.get("currency")
            or UserSettings.objects.get(user=user).preferred_currency
            or Currency.objects.get(code="USD")
        )
        all_expenses_in_currency = get_expenses_date_range_in_currency(
            queryset,
            currency=currency,
            start_date=start_date,
            end_date=end_date,
        )
        expenses = {
            day: [e for e in all_expenses_in_currency[day] if e.is_expense]
            for day in all_expenses_in_currency
        }
        non_expenses = {
            day: [e for e in all_expenses_in_currency[day] if not e.is_expense]
            for day in all_expenses_in_currency
        }
        timeline_data = {}

        cumulative_expense = Decimal("0.00")
        cumulative_non_expense = Decimal("0.00")

        for day in sorted(all_dates_in_range(start_date, end_date)):
            # Daily expense amount (not cumulative)
            expense_amount = Decimal("0.00")
            if day in expenses:
                for expense in expenses[day]:
                    if expense.amount:
                        expense_amount += expense.amount

            daily_non_expense = Decimal("0.00")
            if day in non_expenses:
                for non_expense in non_expenses[day]:
                    if non_expense.amount:
                        daily_non_expense += non_expense.amount

            cumulative_expense += expense_amount
            cumulative_non_expense += daily_non_expense

            difference = cumulative_non_expense - cumulative_expense

            timeline_data[day] = {
                "expense_amount": cumulative_expense,
                "non_expense_amount": cumulative_non_expense,
                "difference": difference,
            }

        # Convert to list format
        result = [
            {
                "date": day,
                "expense_amount": timeline_data[day]["expense_amount"],
                "non_expense_amount": timeline_data[day]["non_expense_amount"],
                "difference": timeline_data[day]["difference"],
            }
            for day in sorted(timeline_data.keys())
        ]

        serializer = AmortizationTimelineSerializer(result, many=True)
        return Response(serializer.data)
