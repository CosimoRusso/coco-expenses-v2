from expenses.models import (
    Notification,
    SharedExpenseDeletedNotification,
    SharedExpenseModifiedNotification,
    SharedExpenseParticipant,
)
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
    expense_id = serializers.SerializerMethodField()

    def get_created_by(self, participant: SharedExpenseParticipant) -> str:
        creator = participant.shared_expense.created_by
        return f"{creator.first_name} {creator.last_name}"

    def get_is_completed(self, participant: SharedExpenseParticipant) -> bool:
        return self.get_expense_id(participant) is not None

    def get_expense_id(self, participant: SharedExpenseParticipant) -> int | None:
        expenses = participant.expense_set.all()
        return expenses[0].id if expenses else None

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
            "expense_id",
        ]


class SharedExpenseModifiedSerializer(serializers.ModelSerializer):
    description = serializers.CharField(source="shared_expense.description")
    modified_by = serializers.SerializerMethodField()

    def get_modified_by(self, modification: SharedExpenseModifiedNotification) -> str:
        editor = modification.modified_by
        return f"{editor.first_name} {editor.last_name}"

    class Meta:
        model = SharedExpenseModifiedNotification
        fields = [
            "description",
            "modified_by",
            "amount_before",
            "currency_before",
            "amount_after",
            "currency_after",
            "number_participants_before",
            "number_participants_after",
            "you_were_added",
            "you_were_removed",
        ]


class SharedExpenseDeletedSerializer(serializers.ModelSerializer):
    deleted_by = serializers.SerializerMethodField()

    def get_deleted_by(self, deletion: SharedExpenseDeletedNotification) -> str:
        return f"{deletion.deleted_by.first_name} {deletion.deleted_by.last_name}"

    class Meta:
        model = SharedExpenseDeletedNotification
        fields = ["deleted_by", "description", "amount", "currency"]


class NotificationSerializer(serializers.ModelSerializer):
    shared_expense = serializers.SerializerMethodField()
    modification = serializers.SerializerMethodField()
    deletion = serializers.SerializerMethodField()

    def get_shared_expense(self, notification: Notification) -> dict | None:
        """The share of the notified user, while they still take part in it."""
        participant = self._participant(notification)
        if participant is None:
            return None
        return SharedExpenseRequestSerializer(participant).data

    def get_modification(self, notification: Notification) -> dict | None:
        modification = self._modification(notification)
        if modification is None:
            return None
        return SharedExpenseModifiedSerializer(modification).data

    def get_deletion(self, notification: Notification) -> dict | None:
        try:
            deletion = notification.shared_expense_deleted
        except SharedExpenseDeletedNotification.DoesNotExist:
            return None
        return SharedExpenseDeletedSerializer(deletion).data

    def _participant(
        self, notification: Notification
    ) -> SharedExpenseParticipant | None:
        links = notification.sharedexpensenotification_set.all()
        if links:
            return links[0].shared_expense_participant
        modification = self._modification(notification)
        if modification is None:
            return None
        return (
            SharedExpenseParticipant.objects.filter(
                shared_expense=modification.shared_expense, user=notification.user
            )
            .prefetch_related("expense_set")
            .first()
        )

    def _modification(
        self, notification: Notification
    ) -> SharedExpenseModifiedNotification | None:
        try:
            return notification.shared_expense_modified
        except SharedExpenseModifiedNotification.DoesNotExist:
            return None

    class Meta:
        model = Notification
        fields = [
            "id",
            "kind",
            "read_at",
            "created_at",
            "shared_expense",
            "modification",
            "deletion",
        ]
