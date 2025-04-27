from rest_framework import serializers

from expenses.models import Expense
import datetime as dt


class ExpenseSerializer(serializers.ModelSerializer):
    amortization_start_date = serializers.DateField(required=True, allow_null=False)
    amortization_end_date = serializers.DateField(required=True, allow_null=False)
    description = serializers.CharField(required=True, allow_null=False)

    def validate_amortization_start_date(self, value):
        if value < dt.date(2000, 1, 1):
            raise serializers.ValidationError(
                "Amortization start date must be after 1 gen 2000"
            )
        return value

    def validate_amortization_end_date(self, value):
        if value < dt.date(2000, 1, 1):
            raise serializers.ValidationError(
                "Amortization start date must be after 1 gen 2000"
            )
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        attrs["user"] = user
        amortization_start_date = attrs["amortization_start_date"]
        amortization_end_date = attrs["amortization_end_date"]
        if amortization_start_date > amortization_end_date:
            raise serializers.ValidationError(
                "Amortization start date must be before amortization end date"
            )
        if attrs["is_expense"] != attrs["category"].for_expense:
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
        model = Expense
        fields = [
            "expense_date",
            "description",
            "forecast_amount",
            "actual_amount",
            "amortization_start_date",
            "amortization_end_date",
            "category",
            "trip",
            "is_expense",
        ]
        read_only_fields = ("id",)
