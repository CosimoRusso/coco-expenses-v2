import datetime as dt
from collections import defaultdict
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import F, Q, QuerySet
from django.utils import timezone
from expenses.managers import exchange_rate_manager
from expenses.models import Currency, SharedExpense, SharedExpenseParticipant, User
from expenses.sharing import CENT

MOVEMENTS_PER_PERSON = 10


@dataclass(frozen=True)
class Movement:
    """One shared expense with `other`: positive when `other` owes the user their quota."""

    description: str
    date: dt.date
    amount: Decimal
    currency: Currency


@dataclass(frozen=True)
class Balance:
    """What `other` owes the user, net: negative when the user owes `other`."""

    other: User
    amount: Decimal
    movements: list[Movement]


@dataclass(frozen=True)
class _Debt:
    other: User
    shared_expense: SharedExpense
    money: exchange_rate_manager.Money


def balances_of(user: User, currency: Currency) -> list[Balance]:
    """The user's net balance with each person they share expenses with, in `currency`.

    The creator of a shared expense paid for all of it, so every other participant
    owes the creator their quota. Each balance lists the latest shared expenses with
    that person, in their own currency.
    """
    debts = _owed_to(user) + _owed_by(user)
    totals = _converted_totals(debts, currency)
    movements = _latest_movements(debts)
    balances = [
        Balance(
            other=other,
            amount=total.quantize(CENT, rounding=ROUND_HALF_UP),
            movements=movements[other],
        )
        for other, total in totals.items()
    ]
    return sorted(balances, key=_by_name)


def shared_expenses_with(
    user: User, other_id: int
) -> QuerySet[SharedExpenseParticipant]:
    """The quotas owed between the user and another person, newest first."""
    owed_to_user = Q(shared_expense__created_by=user, user_id=other_id)
    owed_by_user = Q(shared_expense__created_by_id=other_id, user=user)
    return (
        SharedExpenseParticipant.objects.filter(owed_to_user | owed_by_user)
        .exclude(user=F("shared_expense__created_by"))
        .select_related("shared_expense__currency")
        .order_by("-shared_expense__created_at", "-shared_expense__id")
    )


def movement_of(participant: SharedExpenseParticipant, user: User) -> Movement:
    """The participant's quota as seen by the user, who is on either side of it."""
    shared_expense = participant.shared_expense
    sign = 1 if shared_expense.created_by_id == user.id else -1
    return _movement(shared_expense, _quota(participant, sign))


def _converted_totals(debts: list[_Debt], currency: Currency) -> dict[User, Decimal]:
    """The sum of the debts with each person, converted to `currency`."""
    converted = exchange_rate_manager.bulk_convert_to_currency(
        [debt.money for debt in debts], currency
    )
    totals: dict[User, Decimal] = defaultdict(Decimal)
    for debt, money in zip(debts, converted):
        totals[debt.other] += money.amount
    return totals


def _latest_movements(debts: list[_Debt]) -> dict[User, list[Movement]]:
    """The newest `MOVEMENTS_PER_PERSON` debts with each person, newest first."""
    movements: dict[User, list[Movement]] = defaultdict(list)
    for debt in sorted(debts, key=_by_recency, reverse=True):
        if len(movements[debt.other]) < MOVEMENTS_PER_PERSON:
            movements[debt.other].append(_movement(debt.shared_expense, debt.money))
    return movements


def _movement(
    shared_expense: SharedExpense, money: exchange_rate_manager.Money
) -> Movement:
    return Movement(
        description=shared_expense.description,
        date=money.day,
        amount=money.amount,
        currency=money.currency,
    )


def _by_recency(debt: _Debt) -> tuple[dt.datetime, int]:
    return (debt.shared_expense.created_at, debt.shared_expense.id)


def _owed_to(user: User) -> list[_Debt]:
    """Quotas other participants owe the user for shared expenses the user created."""
    participants = (
        SharedExpenseParticipant.objects.filter(shared_expense__created_by=user)
        .exclude(user=user)
        .select_related("user", "shared_expense__currency")
    )
    return [
        _Debt(other=p.user, shared_expense=p.shared_expense, money=_quota(p, sign=1))
        for p in participants
    ]


def _owed_by(user: User) -> list[_Debt]:
    """Quotas the user owes the creators of shared expenses created by others."""
    participants = (
        SharedExpenseParticipant.objects.filter(user=user)
        .exclude(shared_expense__created_by=user)
        .select_related("shared_expense__created_by", "shared_expense__currency")
    )
    return [
        _Debt(
            other=p.shared_expense.created_by,
            shared_expense=p.shared_expense,
            money=_quota(p, sign=-1),
        )
        for p in participants
    ]


def _quota(
    participant: SharedExpenseParticipant, sign: int
) -> exchange_rate_manager.Money:
    """The participant's quota, dated on the day the shared expense was created."""
    shared_expense = participant.shared_expense
    return exchange_rate_manager.Money(
        amount=sign * participant.quota,
        currency=shared_expense.currency,
        day=timezone.localdate(shared_expense.created_at),
    )


def _by_name(balance: Balance) -> tuple[str, str, int]:
    return (balance.other.first_name, balance.other.last_name, balance.other.id)
