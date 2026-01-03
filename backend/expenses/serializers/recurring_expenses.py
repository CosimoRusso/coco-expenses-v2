import datetime as dt

from expenses.models import RecurringExpense
from rest_framework import serializers


class RecurringExpenseSerializer(serializers.ModelSerializer):
    start_date = serializers.DateField(required=True, allow_null=False)
    description = serializers.CharField(required=True, allow_null=False)
    schedule = serializers.CharField(required=True, allow_null=False)
    amortization_duration = serializers.IntegerField(
        required=False, allow_null=False, min_value=1
    )
    amortization_unit = serializers.ChoiceField(
        required=False,
        allow_null=False,
        choices=["DAY", "WEEK", "MONTH", "YEAR"],
    )

    def validate_start_date(self, value):
        if value < dt.date(2000, 1, 1):
            raise serializers.ValidationError("Start date must be after 1 gen 2000")
        return value

    def validate_end_date(self, value):
        if value is not None and value < dt.date(2000, 1, 1):
            raise serializers.ValidationError("End date must be after 1 gen 2000")
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        attrs["user"] = user
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")

        # Use instance values for partial updates
        if self.instance:
            if start_date is None:
                start_date = self.instance.start_date
            if end_date is None and "end_date" not in attrs:
                end_date = self.instance.end_date

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                "Start date must be before or equal to end date"
            )

        # Check category coherence - handle both create and update
        is_expense = attrs.get("is_expense")
        category = attrs.get("category")

        if self.instance:
            if is_expense is None:
                is_expense = self.instance.is_expense
            if category is None:
                category = self.instance.category

        if is_expense is not None and category:
            if is_expense != category.for_expense:
                raise serializers.ValidationError(
                    "Category is incoherent with expense type"
                )
        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().update(instance, validated_data)

    class Meta:
        model = RecurringExpense
        fields = [
            "id",
            "start_date",
            "end_date",
            "amount",
            "category",
            "trip",
            "schedule",
            "description",
            "is_expense",
            "currency",
            "amortization_duration",
            "amortization_unit",
        ]
        read_only_fields = ["id"]
