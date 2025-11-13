from django.db.models import QuerySet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from expenses.date_utils import all_dates_in_range
from expenses.models import Expense, ExpenseCategory
from expenses.serializers.statistics import (
    StartEndDateSerializer,
    CategoryStatisticsSerializer,
)
from expenses.statistics_utils import get_expenses_date_range


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
        categories = ExpenseCategory.objects.filter(user=request.user)
        input_serializer = StartEndDateSerializer(data=request.query_params)
        input_serializer.is_valid(raise_exception=True)
        start_date = input_serializer.validated_data["start_date"]
        end_date = input_serializer.validated_data["end_date"]
        expenses = get_expenses_date_range(
            queryset,
            start_date=start_date,
            end_date=end_date,
        )
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
                "amount": data["amount"],
            }
            for category, data in result.items()
        ]

        serializer = CategoryStatisticsSerializer(result, many=True)
        response = list(
            sorted(serializer.data, key=lambda item: item["category"]["name"])
        )
        return Response(response)
