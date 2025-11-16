from rest_framework import serializers

from expenses.serializers.expense_categories import ExpenseCategorySerializer


class StartEndDateSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=True, allow_null=False)
    end_date = serializers.DateField(required=True, allow_null=False)

    def validate(self, attrs):
        if attrs["start_date"] > attrs["end_date"]:
            raise serializers.ValidationError("Start date cannot be after end date.")
        return attrs


class CategoryStatisticsSerializer(serializers.Serializer):
    category = ExpenseCategorySerializer()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)


class AmortizationTimelineSerializer(serializers.Serializer):
    expense_amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    non_expense_amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    difference = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    date = serializers.DateField()
