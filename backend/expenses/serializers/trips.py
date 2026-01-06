from rest_framework import serializers

from expenses.models import Settings, Trip


class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = [
            "id",
            "code",
            "name",
            "is_active",
        ]

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["user"] = user
        
        # Check limit from settings
        settings = Settings.objects.first()
        if settings and settings.max_trips is not None:
            current_count = Trip.objects.filter(user=user).count()
            if current_count >= settings.max_trips:
                raise serializers.ValidationError(
                    f"Cannot create new trip. Maximum number of trips ({settings.max_trips}) has been reached."
                )
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().update(instance, validated_data)
