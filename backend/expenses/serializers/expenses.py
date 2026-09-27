import datetime as dt

from django.db import transaction
from expenses.models import Expense, SharedExpenseParticipant
from expenses.models.friend import friends_of
from expenses.models.user import User
from expenses.models.user_settings import UserSettings
from expenses.serializers.shared_expenses import SharedExpenseSummarySerializer
from expenses.sharing import (
    ExpenseShare,
    InvalidSplit,
    SharedExpenseChange,
    Split,
    apply_shared_expense_change,
    create_shared_expense,
)
from expenses.utils.encryption.encryption import (
    decrypt_text_with_key,
    encrypt_text_with_key,
)
from rest_framework import serializers


class QuotaSerializer(serializers.Serializer):
    user = serializers.IntegerField()
    quota = serializers.DecimalField(max_digits=10, decimal_places=2)


class ExpenseSerializer(serializers.ModelSerializer):
    amortization_start_date = serializers.DateField(required=True, allow_null=False)
    amortization_end_date = serializers.DateField(required=True, allow_null=False)
    description = serializers.CharField(required=True, allow_null=False)
    shared_with = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True, write_only=True, required=False
    )
    # The quota of every participant; without it the total is split equally
    split = serializers.ListField(
        child=QuotaSerializer(), write_only=True, required=False, allow_empty=False
    )
    shared_expense = serializers.SerializerMethodField()

    def validate_amortization_start_date(self, value):
        if value < dt.date(2000, 1, 1):
            raise serializers.ValidationError(
                "Amortization start date must be after 1 gen 2000"
            )
        return value

    def validate_amortization_end_date(self, value):
        if value < dt.date(2000, 1, 1):
            raise serializers.ValidationError(
                "Amortization end date must be after 1 gen 2000"
            )
        return value

    def validate_shared_with(self, others: list[User]) -> list[User]:
        """Each person can appear only once."""
        other_ids = [other.id for other in others]
        if len(set(other_ids)) != len(other_ids):
            raise serializers.ValidationError(
                "An expense can be shared only once with each person"
            )
        return others

    def validate_split(self, quotas: list[dict]) -> Split:
        """Each person can have only one quota."""
        split = {quota["user"]: quota["quota"] for quota in quotas}
        if len(split) != len(quotas):
            raise serializers.ValidationError("Each person can have only one quota")
        return split

    def validate_payment_method(self, payment_method):
        """A user can only use their own payment methods."""
        if payment_method is None:
            return None
        if payment_method.user_id != self.context["request"].user.id:
            raise serializers.ValidationError("Invalid payment method")
        return payment_method

    def validate_shared_expense_participant(self, participant):
        """A user completes only their own share, and only once."""
        if self.instance is not None:
            return self.instance.shared_expense_participant
        if participant is None:
            return None
        if participant.user_id != self.context["request"].user.id:
            raise serializers.ValidationError("Invalid shared expense")
        if Expense.objects.filter(shared_expense_participant=participant).exists():
            raise serializers.ValidationError(
                "This shared expense is already completed"
            )
        return participant

    def validate(self, attrs):
        user = self.context["request"].user
        attrs["user"] = user
        amortization_start_date = attrs["amortization_start_date"]
        amortization_end_date = attrs["amortization_end_date"]
        if amortization_start_date > amortization_end_date:
            raise serializers.ValidationError(
                "Amortization start date must be before amortization end date"
            )
        if attrs["is_expense"] != attrs["category"].for_expense:
            raise serializers.ValidationError(
                "Category is incoherent with expense type"
            )

        self._apply_sharing(attrs)

        user_settings = UserSettings.objects.get_or_create(user=user)[0]
        if user_settings.is_encrypted:
            self._encrypt(attrs)
        return attrs

    def _apply_sharing(self, attrs) -> None:
        """Validate the sharing requested and set the amount to the user's own quota.

        For a shared expense, the amount received is the total shared.
        """
        others = attrs.pop("shared_with", None)
        if self._is_shared():
            attrs["share_change"] = self._change_shared_expense(others, attrs)
            attrs["amount"] = attrs["share_change"].quotas()[attrs["user"].id]
        elif others:
            attrs["share"] = self._share_with(others, attrs)
            attrs["amount"] = attrs["share"].quotas()[attrs["user"].id]
        elif "split" in attrs:
            raise serializers.ValidationError("Only a shared expense can be split")
        elif attrs.get("shared_expense_participant") and self.instance is None:
            self._check_matches_quota(attrs)

    def _is_shared(self) -> bool:
        """Whether this is an update of an expense already part of a shared expense."""
        return (
            self.instance is not None
            and self.instance.shared_expense_participant_id is not None
        )

    def _share_with(self, friends: list[User], attrs) -> ExpenseShare:
        """The share of this expense between the current user and `friends`."""
        if attrs.get("shared_expense_participant"):
            raise serializers.ValidationError(
                "An expense completing a shared expense cannot be shared again"
            )
        self._check_amount_and_currency(attrs)
        if not {friend.id for friend in friends} <= self._friend_ids(attrs["user"]):
            raise serializers.ValidationError(
                "An expense can be shared only with your friends"
            )
        share = ExpenseShare(
            creator=attrs["user"],
            friends=friends,
            description=attrs["description"],
            total=attrs["amount"],
            currency=attrs["currency"],
            split=attrs.pop("split", None),
        )
        self._check_split(share)
        return share

    def _change_shared_expense(
        self, others: list[User] | None, attrs
    ) -> SharedExpenseChange:
        """The edit of the shared expense, keeping its participants when none are sent."""
        self._check_amount_and_currency(attrs)
        shared_expense = self.instance.shared_expense_participant.shared_expense
        editor = attrs["user"]
        current_others = [
            participant.user
            for participant in shared_expense.sharedexpenseparticipant_set.all()
            if participant.user_id != editor.id
        ]
        if others is None:
            others = current_others
        self._check_participants(shared_expense, editor, others, current_others)
        change = SharedExpenseChange(
            shared_expense=shared_expense,
            editor=editor,
            others=others,
            total=attrs["amount"],
            currency=attrs["currency"],
            split=attrs.pop("split", None),
        )
        self._check_split(change)
        return change

    def _check_split(self, share: ExpenseShare | SharedExpenseChange) -> None:
        try:
            share.check()
        except InvalidSplit as error:
            raise serializers.ValidationError(str(error)) from error

    def _check_participants(self, shared_expense, editor, others, current_others):
        """The creator and the editor stay, and only the editor's friends can be added."""
        other_ids = {other.id for other in others}
        if not other_ids:
            raise serializers.ValidationError(
                "A shared expense needs at least one other participant"
            )
        if editor.id in other_ids:
            raise serializers.ValidationError(
                "You cannot share an expense with yourself"
            )
        creator_id = shared_expense.created_by_id
        if creator_id != editor.id and creator_id not in other_ids:
            raise serializers.ValidationError(
                "The creator of a shared expense cannot be removed"
            )
        added_ids = other_ids - {other.id for other in current_others}
        if not added_ids <= self._friend_ids(editor):
            raise serializers.ValidationError(
                "Only your friends can be added to a shared expense"
            )

    def _check_amount_and_currency(self, attrs) -> None:
        if attrs.get("amount") is None or attrs.get("currency") is None:
            raise serializers.ValidationError(
                "Amount and currency are required to share an expense"
            )

    def _friend_ids(self, user: User) -> set[int]:
        return set(friends_of(user).values_list("id", flat=True))

    def _check_matches_quota(self, attrs) -> None:
        """An expense completing a share must match the quota and currency assigned."""
        participant: SharedExpenseParticipant = attrs["shared_expense_participant"]
        if attrs.get("amount") != participant.quota:
            raise serializers.ValidationError(
                f"Amount must match your quota of {participant.quota}"
            )
        if attrs.get("currency") != participant.shared_expense.currency:
            raise serializers.ValidationError(
                "Currency must match the currency of the shared expense"
            )

    def _encrypt(self, attrs) -> None:
        """Replace the description and amount with their encrypted versions."""
        user_crypto_key = self.context["request"].COOKIES.get("user_crypto_key")
        if not user_crypto_key:
            raise serializers.ValidationError("User crypto key is missing in cookies")
        user = attrs["user"]
        attrs["encrypted_description"] = encrypt_text_with_key(
            user, user_crypto_key, attrs["description"]
        )
        attrs["encrypted_amount"] = encrypt_text_with_key(
            user, user_crypto_key, str(attrs["amount"])
        )
        attrs["description"] = ""
        attrs["amount"] = None

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        with transaction.atomic():
            self._store_share(validated_data)
            return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["user"] = self.context["request"].user
        with transaction.atomic():
            self._store_share(validated_data)
            return super().update(instance, validated_data)

    def _store_share(self, validated_data) -> None:
        """Create or change the shared expense validated for this expense, if any."""
        share = validated_data.pop("share", None)
        share_change = validated_data.pop("share_change", None)
        if share is not None:
            validated_data["shared_expense_participant"] = create_shared_expense(share)
        if share_change is not None:
            # A fresh participant, so the response does not show the participants
            # prefetched before the change
            validated_data["shared_expense_participant"] = apply_shared_expense_change(
                share_change
            )

    def get_shared_expense(self, expense: Expense) -> dict | None:
        participant = expense.shared_expense_participant
        if participant is None:
            return None
        return SharedExpenseSummarySerializer(participant.shared_expense).data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user: User = self.context["request"].user
        user_settings = UserSettings.objects.get_or_create(user=user)[0]
        if not user_settings.is_encrypted:
            return representation

        user_crypto_key = self.context["request"].COOKIES.get("user_crypto_key")
        if not user_crypto_key:
            raise serializers.ValidationError("User crypto key is missing in cookies")

        representation["description"] = decrypt_text_with_key(
            user, user_crypto_key, instance.encrypted_description
        )
        representation["amount"] = decrypt_text_with_key(
            user, user_crypto_key, instance.encrypted_amount
        )
        return representation

    class Meta:
        model = Expense
        fields = [
            "id",
            "expense_date",
            "description",
            "amount",
            "amortization_start_date",
            "amortization_end_date",
            "category",
            "trip",
            "payment_method",
            "is_expense",
            "currency",
            "shared_with",
            "split",
            "shared_expense_participant",
            "shared_expense",
        ]
        read_only_fields = ["id"]
