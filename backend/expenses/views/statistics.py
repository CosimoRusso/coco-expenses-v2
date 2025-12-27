from decimal import Decimal

from django.db.models import QuerySet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from expenses.date_utils import all_dates_in_range
from expenses.models import Currency, Expense, ExpenseCategory, UserSettings
from expenses.serializers.statistics import (
    StatisticsInputSerializer,
    CategoryStatisticsSerializer,
    AmortizationTimelineSerializer,
)
from expenses.statistics_utils import get_expenses_date_range_in_currency, get_non_expenses_date_range


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
        currency: Currency = input_serializer.validated_data.get("currency") or UserSettings.objects.get(user=user).preferred_currency or Currency.objects.get(code="USD")
        all_expenses_in_currency = get_expenses_date_range_in_currency(
            queryset,
            currency=currency,
            start_date=start_date,
            end_date=end_date,
        )
        expenses = {day: [e for e in all_expenses_in_currency[day] if e.is_expense] for day in all_expenses_in_currency}
        result = {
            category: {"amount": 0}
            for category in categories
        }

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
            sorted(serializer.data, key=lambda item: float(item["amount"]), reverse=True)
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
        currency: Currency = input_serializer.validated_data.get("currency") or UserSettings.objects.get(user=user).preferred_currency or Currency.objects.get(code="USD")
        all_expenses_in_currency = get_expenses_date_range_in_currency(
            queryset,
            currency=currency,
            start_date=start_date,
            end_date=end_date,
        )
        expenses = {day: [e for e in all_expenses_in_currency[day] if e.is_expense] for day in all_expenses_in_currency}
        non_expenses = {day: [e for e in all_expenses_in_currency[day] if not e.is_expense] for day in all_expenses_in_currency}
        timeline_data = {}
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
            
            cumulative_non_expense += daily_non_expense
            
            difference = cumulative_non_expense - expense_amount
            
            timeline_data[day] = {
                "expense_amount": expense_amount,
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
