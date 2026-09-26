from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal

from expenses.models import (
    Currency,
    Notification,
    SharedExpense,
    SharedExpenseNotification,
    SharedExpenseParticipant,
    User,
)
from expenses.models.notification import NotificationKind

CENT = Decimal("0.01")


def split_equally(total: Decimal, parts: int) -> list[Decimal]:
    """Split `total` into `parts` quotas that add up to it exactly.

    The first quota takes the cents left over by rounding down, so it belongs to
    the creator of the shared expense.
    """
    base_quota = (total / parts).quantize(CENT, rounding=ROUND_DOWN)
    leftover = total - base_quota * parts
    return [base_quota + leftover] + [base_quota] * (parts - 1)


@dataclass(frozen=True)
class ExpenseShare:
    """An expense its creator splits equally with some friends."""

    creator: User
    friends: list[User]
    description: str
    total: Decimal
    currency: Currency

    def quotas(self) -> list[Decimal]:
        """The creator's quota first, then one per friend in order."""
        return split_equally(self.total, len(self.friends) + 1)


def create_shared_expense(share: ExpenseShare) -> SharedExpenseParticipant:
    """Store the shared expense and its participants, and ask each friend to complete it.

    Returns the creator's participant, which the creator's own expense points to.
    """
    shared_expense = SharedExpense.objects.create(
        description=share.description,
        amount=share.total,
        currency=share.currency,
        created_by=share.creator,
    )
    creator_quota, *friend_quotas = share.quotas()
    for friend, quota in zip(share.friends, friend_quotas):
        participant = SharedExpenseParticipant.objects.create(
            user=friend, shared_expense=shared_expense, quota=quota
        )
        _notify_share_requested(participant)
    return SharedExpenseParticipant.objects.create(
        user=share.creator, shared_expense=shared_expense, quota=creator_quota
    )


def _notify_share_requested(participant: SharedExpenseParticipant) -> None:
    """Notify a friend that they have a quota of a shared expense to complete."""
    notification = Notification.objects.create(
        user=participant.user, kind=NotificationKind.SHARED_EXPENSE_REQUESTED
    )
    SharedExpenseNotification.objects.create(
        notification=notification, shared_expense_participant=participant
    )
