from backend.expenses import date_utils
from expenses.models.user import get_hashed_password
from rest_framework import serializers

from expenses.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]
        read_only_fields = ["id"]


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(allow_null=False, allow_blank=False, required=True)
    password = serializers.CharField(allow_null=False, allow_blank=False, required=True)


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(allow_null=False, allow_blank=False, required=True)
    password = serializers.CharField(
        allow_null=False, allow_blank=False, required=True, write_only=True
    )

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name"]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def validate_password(self, value):
        if len(value) < 6:
            raise serializers.ValidationError(
                "Password must be at least 6 characters long"
            )
        return value

    def create(self, validated_data):
        password_hash = get_hashed_password(validated_data.pop("password"))
        user = User.objects.create(
            **validated_data,
            password_hash=password_hash,
            email_confirmed_at=date_utils.now(),
        )
        return user
