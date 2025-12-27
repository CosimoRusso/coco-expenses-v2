from rest_framework import serializers

from expenses.serializers.expense_categories import ExpenseCategorySerializer
from expenses.models.currency import Currency


class StatisticsInputSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=True, allow_null=False)
    end_date = serializers.DateField(required=True, allow_null=False)
    currency = serializers.PrimaryKeyRelatedField(
        queryset=Currency.objects.all(), required=False, allow_null=True
    )

    def validate(self, attrs):
        if attrs["start_date"] > attrs["end_date"]:
            raise serializers.ValidationError("Start date cannot be after end date.")
        return attrs


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ["id", "code", "symbol", "display_name"]
        read_only_fields = ["id", "code", "symbol", "display_name"]


class CategoryStatisticsSerializer(serializers.Serializer):
    category = ExpenseCategorySerializer()
    currency = CurrencySerializer()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)


class AmortizationTimelineSerializer(serializers.Serializer):
    expense_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    non_expense_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    difference = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    date = serializers.DateField()
