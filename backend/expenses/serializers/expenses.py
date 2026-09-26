import datetime as dt

from django.db import transaction
from expenses.models import Expense, SharedExpenseParticipant
from expenses.models.friend import friends_of
from expenses.models.user import User
from expenses.models.user_settings import UserSettings
from expenses.sharing import ExpenseShare, create_shared_expense
from expenses.utils.encryption.encryption import (
    decrypt_text_with_key,
    encrypt_text_with_key,
)
from rest_framework import serializers


class ExpenseSerializer(serializers.ModelSerializer):
    amortization_start_date = serializers.DateField(required=True, allow_null=False)
    amortization_end_date = serializers.DateField(required=True, allow_null=False)
    description = serializers.CharField(required=True, allow_null=False)
    shared_with = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True, write_only=True, required=False
    )

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

    def validate_shared_with(self, friends: list[User]) -> list[User]:
        """Only a new expense can be shared, once per friend, and only with friends."""
        if friends and self.instance is not None:
            raise serializers.ValidationError("An existing expense cannot be shared")
        friend_ids = [friend.id for friend in friends]
        user_friend_ids = set(
            friends_of(self.context["request"].user).values_list("id", flat=True)
        )
        has_duplicates = len(set(friend_ids)) != len(friend_ids)
        if has_duplicates or not set(friend_ids) <= user_friend_ids:
            raise serializers.ValidationError(
                "An expense can be shared only once with each of your friends"
            )
        return friends

    def validate_shared_expense_participant(self, participant):
        """A user completes only their own share, and only once."""
        if self.instance is not None:
            return self.instance.shared_expense_participant
        if participant is None:
            return None
        if participant.user_id != self.context["request"].user.id:
            raise serializers.ValidationError("Invalid shared expense")
        if Expense.objects.filter(shared_expense_participant=participant).exists():
            raise serializers.ValidationError("This shared expense is already completed")
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

        friends = attrs.pop("shared_with", [])
        if friends:
            attrs["share"] = self._share_with(friends, attrs)
            attrs["amount"] = attrs["share"].quotas()[0]
        if attrs.get("shared_expense_participant") and self.instance is None:
            self._check_matches_quota(attrs)

        user_settings = UserSettings.objects.get_or_create(user=user)[0]
        if user_settings.is_encrypted:
            self._encrypt(attrs)
        return attrs

    def _share_with(self, friends: list[User], attrs) -> ExpenseShare:
        """The share of this expense between the current user and `friends`."""
        if attrs.get("shared_expense_participant"):
            raise serializers.ValidationError(
                "An expense completing a shared expense cannot be shared again"
            )
        if attrs.get("amount") is None or attrs.get("currency") is None:
            raise serializers.ValidationError(
                "Amount and currency are required to share an expense"
            )
        return ExpenseShare(
            creator=attrs["user"],
            friends=friends,
            description=attrs["description"],
            total=attrs["amount"],
            currency=attrs["currency"],
        )

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
        share = validated_data.pop("share", None)
        with transaction.atomic():
            if share is not None:
                validated_data["shared_expense_participant"] = create_shared_expense(
                    share
                )
            return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().update(instance, validated_data)

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
            "is_expense",
            "currency",
            "shared_with",
            "shared_expense_participant",
        ]
        read_only_fields = ["id"]
