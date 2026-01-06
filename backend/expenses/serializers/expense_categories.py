from expenses.models import ExpenseCategory, Settings
from rest_framework import serializers


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = [
            "id",
            "code",
            "name",
            "for_expense",
            "is_active",
        ]

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["user"] = user

        # Check limit from settings
        settings = Settings.objects.first()
        if settings and settings.max_categories is not None:
            current_count = ExpenseCategory.objects.filter(user=user).count()
            if current_count >= settings.max_categories:
                raise serializers.ValidationError(
                    f"Cannot create new category. Maximum number of categories ({settings.max_categories}) has been reached."
                )

        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().update(instance, validated_data)
