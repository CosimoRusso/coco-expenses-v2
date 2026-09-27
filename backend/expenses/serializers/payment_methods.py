from expenses.models import PaymentMethod
from rest_framework import serializers


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ["id", "code", "name", "is_active"]

    def validate_code(self, code: str) -> str:
        """A user cannot have two payment methods with the same code."""
        user = self.context["request"].user
        duplicates = PaymentMethod.objects.filter(user=user, code=code)
        if self.instance is not None:
            duplicates = duplicates.exclude(id=self.instance.id)
        if duplicates.exists():
            raise serializers.ValidationError(
                "A payment method with this code already exists"
            )
        return code

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
