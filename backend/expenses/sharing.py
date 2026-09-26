from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal

from expenses.models import (
    Currency,
    Expense,
    Notification,
    SharedExpense,
    SharedExpenseDeletedNotification,
    SharedExpenseModifiedNotification,
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


# Quotas by user id
Split = dict[int, Decimal]


class InvalidSplit(ValueError):
    """A split that does not divide the total between the participants."""


def quotas_of(total: Decimal, user_ids: list[int], split: Split | None) -> Split:
    """The quotas of `split`, or `total` split equally when it is None.

    In an equal split the first user, the creator, takes the leftover cents.
    """
    if split is not None:
        return dict(split)
    return dict(zip(user_ids, split_equally(total, len(user_ids))))


def check_quotas(quotas: Split, user_ids: list[int], total: Decimal) -> None:
    """Each participant has a quota and they add up to `total`.

    Anyone's quota can be zero, the creator's too: they may have paid for the others.
    """
    if set(quotas) != set(user_ids):
        raise InvalidSplit("The split must give a quota to each participant")
    if sum(quotas.values()) != total:
        raise InvalidSplit(f"The quotas must add up to the total of {total}")
    if any(quota < 0 for quota in quotas.values()):
        raise InvalidSplit("A quota cannot be negative")


@dataclass(frozen=True)
class ExpenseShare:
    """An expense its creator splits with some friends, equally unless `split` is given."""

    creator: User
    friends: list[User]
    description: str
    total: Decimal
    currency: Currency
    split: Split | None = None

    def user_ids(self) -> list[int]:
        """The creator first, then each friend in order."""
        return [self.creator.id, *(friend.id for friend in self.friends)]

    def quotas(self) -> Split:
        return quotas_of(self.total, self.user_ids(), self.split)

    def check(self) -> None:
        check_quotas(self.quotas(), self.user_ids(), self.total)


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
    quotas = share.quotas()
    for friend in share.friends:
        participant = SharedExpenseParticipant.objects.create(
            user=friend, shared_expense=shared_expense, quota=quotas[friend.id]
        )
        _notify_share_requested(participant)
    return SharedExpenseParticipant.objects.create(
        user=share.creator,
        shared_expense=shared_expense,
        quota=quotas[share.creator.id],
    )


def _notify_share_requested(participant: SharedExpenseParticipant) -> None:
    """Notify a friend that they have a quota of a shared expense to complete."""
    notification = Notification.objects.create(
        user=participant.user, kind=NotificationKind.SHARED_EXPENSE_REQUESTED
    )
    SharedExpenseNotification.objects.create(
        notification=notification, shared_expense_participant=participant
    )


@dataclass(frozen=True)
class SharedExpenseChange:
    """A participant's edit of what everyone shares: the total, currency, participants and
    split, which is equal unless `split` is given."""

    shared_expense: SharedExpense
    editor: User
    # Every participant after the change, except the editor
    others: list[User]
    total: Decimal
    currency: Currency
    split: Split | None = None

    def participants(self) -> list[User]:
        """Everyone sharing the expense after the change, its creator first."""
        creator = self.shared_expense.created_by
        everyone_else = [
            user for user in [self.editor, *self.others] if user.id != creator.id
        ]
        return [creator, *everyone_else]

    def user_ids(self) -> list[int]:
        return [user.id for user in self.participants()]

    def quotas(self) -> Split:
        return quotas_of(self.total, self.user_ids(), self.split)

    def check(self) -> None:
        check_quotas(self.quotas(), self.user_ids(), self.total)


@dataclass(frozen=True)
class _SharedState:
    total: Decimal
    currency: Currency
    quotas: Split

    @property
    def user_ids(self) -> frozenset[int]:
        return frozenset(self.quotas)


def apply_shared_expense_change(
    change: SharedExpenseChange,
) -> SharedExpenseParticipant:
    """Apply the change, store the new quotas and notify everyone else involved.

    Expenses of the other participants keep their amount until they save them again.
    Returns the editor's participant.
    """
    shared_expense = change.shared_expense
    before = _shared_state(shared_expense)
    after = _SharedState(change.total, change.currency, change.quotas())
    if before != after:
        shared_expense.amount = change.total
        shared_expense.currency = change.currency
        shared_expense.save(update_fields=["amount", "currency", "updated_at"])
        _remove_participants(shared_expense, before.user_ids - after.user_ids)
        _store_quotas(change)
        _notify_modified(change, before, after)
    return SharedExpenseParticipant.objects.get(
        shared_expense=shared_expense, user=change.editor
    )


def _shared_state(shared_expense: SharedExpense) -> _SharedState:
    quotas = shared_expense.sharedexpenseparticipant_set.values_list("user_id", "quota")
    return _SharedState(shared_expense.amount, shared_expense.currency, dict(quotas))


def _remove_participants(
    shared_expense: SharedExpense, user_ids: frozenset[int]
) -> None:
    """Remove the participants with their expense and their pending share request."""
    participants = SharedExpenseParticipant.objects.filter(
        shared_expense=shared_expense, user_id__in=user_ids
    )
    Expense.objects.filter(shared_expense_participant__in=participants).delete()
    requests = SharedExpenseNotification.objects.filter(
        shared_expense_participant__in=participants
    )
    request_notification_ids = list(requests.values_list("notification_id", flat=True))
    requests.delete()
    Notification.objects.filter(id__in=request_notification_ids).delete()
    participants.delete()


def _store_quotas(change: SharedExpenseChange) -> None:
    """Set each participant's new quota, adding the participants who were not there."""
    for user_id, quota in change.quotas().items():
        SharedExpenseParticipant.objects.update_or_create(
            shared_expense=change.shared_expense,
            user_id=user_id,
            defaults={"quota": quota},
        )


def _notify_modified(
    change: SharedExpenseChange, before: _SharedState, after: _SharedState
) -> None:
    """Tell everyone involved before or after the change, except the editor, what changed."""
    recipients = (before.user_ids | after.user_ids) - {change.editor.id}
    for user_id in recipients:
        notification = Notification.objects.create(
            user_id=user_id, kind=NotificationKind.SHARED_EXPENSE_MODIFIED
        )
        SharedExpenseModifiedNotification.objects.create(
            notification=notification,
            shared_expense=change.shared_expense,
            modified_by=change.editor,
            amount_before=before.total,
            currency_before=before.currency,
            amount_after=after.total,
            currency_after=after.currency,
            number_participants_before=len(before.user_ids),
            number_participants_after=len(after.user_ids),
            you_were_added=user_id not in before.user_ids,
            you_were_removed=user_id not in after.user_ids,
        )


def delete_shared_expense(shared_expense: SharedExpense, deleted_by: User) -> None:
    """Delete the shared expense with every participant's expense, and notify the others.

    Notifications about the shared expense go too, as they would point to nothing.
    """
    participants = shared_expense.sharedexpenseparticipant_set.all()
    for participant in participants:
        if participant.user_id != deleted_by.id:
            _notify_deleted(shared_expense, deleted_by, participant.user_id)
    Expense.objects.filter(shared_expense_participant__in=participants).delete()
    _delete_notifications_about(shared_expense)
    participants.delete()
    shared_expense.delete()


def _notify_deleted(
    shared_expense: SharedExpense, deleted_by: User, user_id: int
) -> None:
    notification = Notification.objects.create(
        user_id=user_id, kind=NotificationKind.SHARED_EXPENSE_DELETED
    )
    SharedExpenseDeletedNotification.objects.create(
        notification=notification,
        deleted_by=deleted_by,
        description=shared_expense.description,
        amount=shared_expense.amount,
        currency=shared_expense.currency,
    )


def _delete_notifications_about(shared_expense: SharedExpense) -> None:
    """Delete the share requests and modification notifications of the shared expense."""
    requests = SharedExpenseNotification.objects.filter(
        shared_expense_participant__shared_expense=shared_expense
    )
    modifications = SharedExpenseModifiedNotification.objects.filter(
        shared_expense=shared_expense
    )
    notification_ids = [
        *requests.values_list("notification_id", flat=True),
        *modifications.values_list("notification_id", flat=True),
    ]
    requests.delete()
    modifications.delete()
    Notification.objects.filter(id__in=notification_ids).delete()
