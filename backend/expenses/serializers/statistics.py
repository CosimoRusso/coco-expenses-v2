from rest_framework import serializers

from expenses.serializers.expense_categories import ExpenseCategorySerializer


class CategoryStatisticsSerializer(serializers.Serializer):
    category = ExpenseCategorySerializer()
    actual_amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    forecast_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
