from expenses.models.user import User
from expenses.models.user_settings import UserSettings
from rest_framework import serializers


class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = ["id", "user", "preferred_currency", "active_trip"]
        read_only_fields = ["id", "user"]


class UserActivateEncryptionSerializer(serializers.Serializer):
    password = serializers.CharField(allow_null=False, allow_blank=False, required=True)

    def validate_password(self, value: str) -> str:
        user: User = self.context["request"].user
        password = value

        if not user.check_password(password):
            raise serializers.ValidationError("Password incorrect")

        return value
