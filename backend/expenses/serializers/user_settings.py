from expenses.models.user import User
from expenses.models.user_settings import UserSettings
from rest_framework import serializers


class UserSettingsSerializer(serializers.ModelSerializer):
    statistics_start_date = serializers.DateField(read_only=True)
    statistics_end_date = serializers.DateField(read_only=True)

    class Meta:
        model = UserSettings
        fields = [
            "id",
            "user",
            "preferred_currency",
            "active_trip",
            "is_encrypted",
            "default_statistics_start_date",
            "default_statistics_end_date",
            "statistics_start_date",
            "statistics_end_date",
        ]
        read_only_fields = ["id", "user", "is_encrypted"]

    def validate(self, attrs):
        """The statistics period, once the missing dates are defaulted, must not be empty."""
        settings = UserSettings(
            default_statistics_start_date=self._new_value(
                attrs, "default_statistics_start_date"
            ),
            default_statistics_end_date=self._new_value(
                attrs, "default_statistics_end_date"
            ),
        )
        if settings.statistics_start_date > settings.statistics_end_date:
            raise serializers.ValidationError(
                "The statistics start date cannot be after the end date."
            )
        return attrs

    def _new_value(self, attrs, field: str):
        return attrs.get(field, getattr(self.instance, field, None))


class UserActivateEncryptionSerializer(serializers.Serializer):
    password = serializers.CharField(allow_null=False, allow_blank=False, required=True)

    def validate_password(self, value: str) -> str:
        user: User = self.context["request"].user
        password = value

        if not user.check_password(password):
            raise serializers.ValidationError("Password incorrect")

        return value
