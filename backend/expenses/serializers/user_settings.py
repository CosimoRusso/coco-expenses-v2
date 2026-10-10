from expenses.models.user import User
from expenses.models.user_settings import UserSettings
from rest_framework import serializers

STATISTICS_PERIOD_FIELDS = [
    "default_statistics_method",
    "default_statistics_start_date",
    "default_statistics_end_date",
    "default_statistics_n_days_ago_from",
    "default_statistics_n_days_ago_to",
]


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
            *STATISTICS_PERIOD_FIELDS,
            "statistics_start_date",
            "statistics_end_date",
        ]
        read_only_fields = ["id", "user", "is_encrypted"]

    def validate(self, attrs):
        """The statistics period, once the missing values are defaulted, must not be empty."""
        settings = self._settings_after_save(attrs)
        if settings.statistics_start_date > settings.statistics_end_date:
            raise serializers.ValidationError(
                "The statistics start date cannot be after the end date."
            )
        return attrs

    def _settings_after_save(self, attrs) -> UserSettings:
        """Unsaved settings holding the statistics period as the save will leave it."""
        current = {}
        if self.instance:
            current = {
                field: getattr(self.instance, field)
                for field in STATISTICS_PERIOD_FIELDS
            }
        incoming = {
            field: attrs[field] for field in STATISTICS_PERIOD_FIELDS if field in attrs
        }
        return UserSettings(**{**current, **incoming})


class UserActivateEncryptionSerializer(serializers.Serializer):
    password = serializers.CharField(allow_null=False, allow_blank=False, required=True)

    def validate_password(self, value: str) -> str:
        user: User = self.context["request"].user
        password = value

        if not user.check_password(password):
            raise serializers.ValidationError("Password incorrect")

        return value
