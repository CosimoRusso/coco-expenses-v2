import datetime as dt

from expenses.models import Expense
from expenses.models.user import User
from expenses.models.user_settings import UserSettings
from expenses.utils.encryption.encryption import (
    decrypt_text_with_key,
    encrypt_text_with_key,
)
from rest_framework import serializers


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
                "Amortization end date must be after 1 gen 2000"
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

        user: User = self.context["request"].user
        user_settings = UserSettings.objects.get_or_create(user=user)[0]
        if not user_settings.is_encrypted:
            return attrs

        # -- Encrypted management from here --
        user_crypto_key = self.context["request"].COOKIES.get("user_crypto_key")
        if not user_crypto_key:
            raise serializers.ValidationError("User crypto key is missing in cookies")
        attrs["encrypted_description"] = encrypt_text_with_key(
            user, user_crypto_key, attrs["description"]
        )
        attrs["encrypted_amount"] = encrypt_text_with_key(
            user, user_crypto_key, str(attrs["amount"])
        )
        attrs["description"] = ""
        attrs["amount"] = None
        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user: User = self.context["request"].user
        user_settings = UserSettings.objects.get_or_create(user=user)[0]
        if not user_settings.is_encrypted:
            return representation

        user_crypto_key = self.context["request"].COOKIES.get("user_crypto_key")
        if not user_crypto_key:
            raise serializers.ValidationError("User crypto key is missing in cookies")

        representation["description"] = decrypt_text_with_key(
            user, user_crypto_key, instance.encrypted_description
        )
        representation["amount"] = decrypt_text_with_key(
            user, user_crypto_key, instance.encrypted_amount
        )
        return representation

    class Meta:
        model = Expense
        fields = [
            "id",
            "expense_date",
            "description",
            "amount",
            "amortization_start_date",
            "amortization_end_date",
            "category",
            "trip",
            "is_expense",
            "currency",
        ]
        read_only_fields = ["id"]
