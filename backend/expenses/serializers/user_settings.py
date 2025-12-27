from rest_framework import serializers
from expenses.models.user_settings import UserSettings


class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = ["id", "user", "preferred_currency", "active_trip"]
        read_only_fields = ["id", "user"]
