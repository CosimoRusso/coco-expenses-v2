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
    get_expenses_by_day,
    get_expenses_date_range_in_currency,
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

        # Initialize result with all trips and None for expenses without a trip
        trip_amounts = {
            trip: {
                "amount_in_dates": Decimal("0.00"),
                "total_amount": Decimal("0.00"),
                "start_date": None,
                "end_date": None,
                "duration": None,
                "price_per_day": None,
            }
            for trip in trips
        }
        trip_amounts[None] = {
            "amount_in_dates": Decimal("0.00"),
            "total_amount": Decimal("0.00"),
            "start_date": None,
            "end_date": None,
            "duration": None,
            "price_per_day": None,
        }

        for expense in expenses_in_currency:
            current_trip = trip_amounts[expense.trip]
            # Total amount
            current_trip["total_amount"] += expense.amount

            # Trip start date
            if (
                current_trip["start_date"] is None
                or expense.amortization_end_date < current_trip["start_date"]
            ):
                current_trip["start_date"] = expense.amortization_start_date

            # Trip end date
            if (
                current_trip["end_date"] is None
                or current_trip["end_date"] < expense.amortization_end_date
            ):
                current_trip["end_date"] = expense.amortization_end_date

        # Trip duration
        for trip, data in trip_amounts.items():
            if data["end_date"] and data["start_date"]:
                data["duration"] = (data["end_date"] - data["start_date"]).days + 1
            else:
                data["duration"] = 0
            if data["duration"] > 0:
                data["price_per_day"] = data["total_amount"] / data["duration"]

        expenses_by_day = get_expenses_by_day(expenses_in_currency)
        for day in all_dates_in_range(start_date, end_date):
            for expense in expenses_by_day[day]:
                trip_amounts[expense.trip]["amount_in_dates"] += expense.amount

        result = []
        for trip, data in trip_amounts.items():
            # Handle None trips by creating a dict representation
            if trip is None:
                trip_general_data = {
                    "id": None,
                    "code": "",
                    "name": "No Trip",
                    "is_active": False,
                }
            else:
                # Use TripSerializer to serialize the trip instance
                from expenses.serializers.trips import TripSerializer

                trip_serializer = TripSerializer(trip)
                trip_general_data = trip_serializer.data

            result.append(
                {
                    **trip_general_data,
                    **data,
                    "currency": currency,
                }
            )

        serializer = TripStatisticsSerializer(result, many=True)
        response = list(
            sorted(
                serializer.data,
                key=lambda item: float(item["total_amount"]),
                reverse=True,
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
