from collections import defaultdict
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from django.utils import timezone
from expenses.managers import exchange_rate_manager
from expenses.models import Currency, SharedExpenseParticipant, User
from expenses.sharing import CENT


@dataclass(frozen=True)
class Balance:
    """What `other` owes the user, net: negative when the user owes `other`."""

    other: User
    amount: Decimal


@dataclass(frozen=True)
class _Debt:
    other: User
    money: exchange_rate_manager.Money


def balances_of(user: User, currency: Currency) -> list[Balance]:
    """The user's net balance with each person they share expenses with, in `currency`.

    The creator of a shared expense paid for all of it, so every other participant
    owes the creator their quota.
    """
    debts = _owed_to(user) + _owed_by(user)
    converted = exchange_rate_manager.bulk_convert_to_currency(
        [debt.money for debt in debts], currency
    )
    totals: dict[User, Decimal] = defaultdict(Decimal)
    for debt, money in zip(debts, converted):
        totals[debt.other] += money.amount
    balances = [
        Balance(other=other, amount=total.quantize(CENT, rounding=ROUND_HALF_UP))
        for other, total in totals.items()
    ]
    return sorted(balances, key=_by_name)


def _owed_to(user: User) -> list[_Debt]:
    """Quotas other participants owe the user for shared expenses the user created."""
    participants = (
        SharedExpenseParticipant.objects.filter(shared_expense__created_by=user)
        .exclude(user=user)
        .select_related("user", "shared_expense__currency")
    )
    return [_Debt(other=p.user, money=_quota(p, sign=1)) for p in participants]


def _owed_by(user: User) -> list[_Debt]:
    """Quotas the user owes the creators of shared expenses created by others."""
    participants = (
        SharedExpenseParticipant.objects.filter(user=user)
        .exclude(shared_expense__created_by=user)
        .select_related("shared_expense__created_by", "shared_expense__currency")
    )
    return [
        _Debt(other=p.shared_expense.created_by, money=_quota(p, sign=-1))
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
