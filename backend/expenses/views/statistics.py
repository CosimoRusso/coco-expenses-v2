from django.db.models import QuerySet
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from expenses.date_utils import all_dates_in_range
from expenses.models import Expense, ExpenseCategory
from expenses.serializers.statistics import CategoryStatisticsSerializer
from expenses.statistics_utils import get_expenses_date_range


class StatisticViewSet(ListAPIView):
    serializer_class = CategoryStatisticsSerializer

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
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        expenses = get_expenses_date_range(
            queryset,
            start_date=start_date,
            end_date=end_date,
        )
        result = {
            category: {"actual_amount": 0, "forecast_amount": 0}
            for category in categories
        }

        for category in categories:
            for day in all_dates_in_range(start_date, end_date):
                if day in expenses:
                    for expense in expenses[day]:
                        if expense.category == category:
                            result[category]["actual_amount"] += expense.actual_amount
                            result[category][
                                "forecast_amount"
                            ] += expense.forecast_amount

        result = [
            {"category": category, "actual_amount": 0, "forecast_amount": 0}
            for category, data in result.items()
        ]

        serializer = self.get_serializer(data=result)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data)
