from expenses.models import SharedExpense, SharedExpenseParticipant
from rest_framework import serializers


class ParticipantSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id")
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")

    class Meta:
        model = SharedExpenseParticipant
        fields = ["id", "user_id", "first_name", "last_name", "quota"]


class SharedExpenseSummarySerializer(serializers.ModelSerializer):
    """The parts of a shared expense every participant shares."""

    total_amount = serializers.DecimalField(
        source="amount", max_digits=10, decimal_places=2
    )
    participants = serializers.SerializerMethodField()

    def get_participants(self, shared_expense: SharedExpense) -> list[dict]:
        participants = sorted(
            shared_expense.sharedexpenseparticipant_set.all(), key=lambda p: p.id
        )
        return ParticipantSerializer(participants, many=True).data

    class Meta:
        model = SharedExpense
        fields = ["id", "total_amount", "currency", "created_by", "participants"]
