from expenses.models import Notification, SharedExpenseParticipant
from rest_framework import serializers


class SharedExpenseRequestSerializer(serializers.ModelSerializer):
    """The share of a shared expense a user is asked to complete."""

    description = serializers.CharField(source="shared_expense.description")
    total_amount = serializers.DecimalField(
        source="shared_expense.amount", max_digits=10, decimal_places=2
    )
    currency = serializers.PrimaryKeyRelatedField(
        source="shared_expense.currency", read_only=True
    )
    created_by = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()

    def get_created_by(self, participant: SharedExpenseParticipant) -> str:
        creator = participant.shared_expense.created_by
        return f"{creator.first_name} {creator.last_name}"

    def get_is_completed(self, participant: SharedExpenseParticipant) -> bool:
        return len(participant.expense_set.all()) > 0

    class Meta:
        model = SharedExpenseParticipant
        fields = [
            "id",
            "quota",
            "description",
            "total_amount",
            "currency",
            "created_by",
            "is_completed",
        ]


class NotificationSerializer(serializers.ModelSerializer):
    shared_expense = serializers.SerializerMethodField()

    def get_shared_expense(self, notification: Notification) -> dict | None:
        links = notification.sharedexpensenotification_set.all()
        if not links:
            return None
        return SharedExpenseRequestSerializer(links[0].shared_expense_participant).data

    class Meta:
        model = Notification
        fields = ["id", "kind", "read_at", "created_at", "shared_expense"]
