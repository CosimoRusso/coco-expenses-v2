"""Statistics over the expenses of a user, in their favourite currency.

The amounts come from the favourite-currency amount stored on each expense, so they
are complete only after `populate_favourite_currency_amounts`.

An expense is spread evenly over the days of its amortization: the part falling in
a period is proportional to the days they share.
"""

import datetime as dt
from collections import defaultdict
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from django.db import connection
from django.db.models import DateField, F, Func, IntegerField, Max, Min, Q, Sum, Value
from django.db.models.functions import Greatest, Least, Round
from expenses.date_utils import all_dates_in_range
from expenses.favourite_currency_cache import MissingCryptoKey, is_encrypted
from expenses.models import Expense, User
from expenses.utils.encryption.encryption import decrypt_text_with_key

ZERO = Decimal("0.00")
CENTS = Decimal("0.01")
ONE_DAY = dt.timedelta(days=1)


@dataclass(frozen=True)
class Period:
    start: dt.date
    end: dt.date


@dataclass
class TripTotals:
    total_amount: Decimal = ZERO
    amount_in_dates: Decimal = ZERO
    start_date: dt.date | None = None
    end_date: dt.date | None = None


@dataclass
class TimelinePoint:
    """The amounts accumulated from the start of the period up to `date`."""

    date: dt.date
    expense_amount: Decimal
    non_expense_amount: Decimal


def statistics_for(
    user: User, crypto_key: str | None = None
) -> "DatabaseStatistics | DecryptedStatistics":
    """The statistics of `user`, computed where their amounts can be read."""
    if not is_encrypted(user):
        return DatabaseStatistics(user)
    if not crypto_key:
        raise MissingCryptoKey()
    return DecryptedStatistics(user, crypto_key)


class _InclusiveDays(Func):
    """The number of days from the second date to the first, both included."""

    template = "(%(expressions)s + 1)"
    arg_joiner = " - "
    output_field = IntegerField()


def _overlapping(period: Period) -> Q:
    return Q(
        amortization_start_date__lte=period.end,
        amortization_end_date__gte=period.start,
    )


def _amount_in(period: Period) -> Round:
    days_in_period = _InclusiveDays(
        Least(F("amortization_end_date"), Value(period.end, DateField())),
        Greatest(F("amortization_start_date"), Value(period.start, DateField())),
    )
    amortization_days = _InclusiveDays(
        F("amortization_end_date"), F("amortization_start_date")
    )
    return Round(
        F("amount_favourite_currency") * days_in_period / amortization_days,
        precision=2,
    )


TIMELINE_SQL = """
    SELECT day,
           ROUND(SUM(expense_amount) OVER (ORDER BY day), 2),
           ROUND(SUM(non_expense_amount) OVER (ORDER BY day), 2)
    FROM (
        SELECT day::date AS day,
               COALESCE(SUM(daily_amount) FILTER (WHERE is_expense), 0)
                   AS expense_amount,
               COALESCE(SUM(daily_amount) FILTER (WHERE NOT is_expense), 0)
                   AS non_expense_amount
        FROM generate_series(%(start)s::date, %(end)s::date, interval '1 day') AS day
        LEFT JOIN (
            SELECT is_expense,
                   amortization_start_date,
                   amortization_end_date,
                   amount_favourite_currency
                       / (amortization_end_date - amortization_start_date + 1)
                       AS daily_amount
            FROM expenses_expense
            WHERE user_id = %(user_id)s
        ) AS amortized
            ON day BETWEEN amortization_start_date AND amortization_end_date
        GROUP BY day
    ) AS daily
    ORDER BY day
"""


class DatabaseStatistics:
    """Statistics aggregated by the database."""

    def __init__(self, user: User):
        self.user = user

    def category_amounts(self, period: Period) -> dict[int, Decimal]:
        """The expenses falling in `period`, by category id."""
        rows = (
            Expense.objects.filter(
                _overlapping(period), user=self.user, is_expense=True
            )
            .values("category_id")
            .annotate(amount=Sum(_amount_in(period)))
        )
        return {row["category_id"]: row["amount"] or ZERO for row in rows}

    def trip_totals(self, period: Period) -> dict[int | None, TripTotals]:
        """The expenses of each trip, by trip id; None gathers those without a trip."""
        rows = (
            Expense.objects.filter(user=self.user, is_expense=True)
            .values("trip_id")
            .annotate(
                total_amount=Sum("amount_favourite_currency"),
                amount_in_dates=Sum(_amount_in(period), filter=_overlapping(period)),
                start_date=Min("amortization_start_date"),
                end_date=Max("amortization_end_date"),
            )
        )
        return {
            row["trip_id"]: TripTotals(
                total_amount=row["total_amount"] or ZERO,
                amount_in_dates=row["amount_in_dates"] or ZERO,
                start_date=row["start_date"],
                end_date=row["end_date"],
            )
            for row in rows
        }

    def timeline(self, period: Period) -> list[TimelinePoint]:
        """The expenses and the incomes accumulated on each day of `period`."""
        params = {"start": period.start, "end": period.end, "user_id": self.user.id}
        with connection.cursor() as cursor:
            cursor.execute(TIMELINE_SQL, params)
            return [TimelinePoint(*row) for row in cursor.fetchall()]


@dataclass
class _DecryptedExpense:
    amount: Decimal
    amortization_start_date: dt.date
    amortization_end_date: dt.date
    category_id: int
    trip_id: int | None
    is_expense: bool

    def daily_amount(self) -> Decimal:
        return self.amount / _inclusive_days(
            self.amortization_start_date, self.amortization_end_date
        )

    def first_day_in(self, period: Period) -> dt.date:
        return max(self.amortization_start_date, period.start)

    def last_day_in(self, period: Period) -> dt.date:
        return min(self.amortization_end_date, period.end)

    def overlaps(self, period: Period) -> bool:
        return self.first_day_in(period) <= self.last_day_in(period)

    def amount_in(self, period: Period) -> Decimal:
        if not self.overlaps(period):
            return ZERO
        days = _inclusive_days(self.first_day_in(period), self.last_day_in(period))
        return _round(self.daily_amount() * days)


def _inclusive_days(first: dt.date, last: dt.date) -> int:
    return (last - first).days + 1


def _round(amount: Decimal) -> Decimal:
    return amount.quantize(CENTS, ROUND_HALF_UP)


class DecryptedStatistics:
    """Statistics aggregated in Python: the database cannot read encrypted amounts."""

    def __init__(self, user: User, crypto_key: str):
        self.user = user
        self.crypto_key = crypto_key

    def category_amounts(self, period: Period) -> dict[int, Decimal]:
        """The expenses falling in `period`, by category id."""
        amounts = defaultdict(lambda: ZERO)
        for expense in self._expenses(is_expense=True):
            amounts[expense.category_id] += expense.amount_in(period)
        return dict(amounts)

    def trip_totals(self, period: Period) -> dict[int | None, TripTotals]:
        """The expenses of each trip, by trip id; None gathers those without a trip."""
        totals = defaultdict(TripTotals)
        for expense in self._expenses(is_expense=True):
            _add_to_trip(totals[expense.trip_id], expense, period)
        return dict(totals)

    def timeline(self, period: Period) -> list[TimelinePoint]:
        """The expenses and the incomes accumulated on each day of `period`."""
        days = all_dates_in_range(period.start, period.end)
        expenses = _accumulated(self._expenses(is_expense=True), period, days)
        incomes = _accumulated(self._expenses(is_expense=False), period, days)
        return [
            TimelinePoint(day, _round(expense), _round(income))
            for day, expense, income in zip(days, expenses, incomes)
        ]

    def _expenses(self, is_expense: bool) -> list[_DecryptedExpense]:
        rows = Expense.objects.filter(
            user=self.user,
            is_expense=is_expense,
            amortization_start_date__isnull=False,
            amortization_end_date__isnull=False,
        ).exclude(encrypted_amount_favourite_currency="")
        return [self._decrypted(row) for row in rows]

    def _decrypted(self, expense: Expense) -> _DecryptedExpense:
        amount = decrypt_text_with_key(
            self.user, self.crypto_key, expense.encrypted_amount_favourite_currency
        )
        return _DecryptedExpense(
            amount=Decimal(amount),
            amortization_start_date=expense.amortization_start_date,
            amortization_end_date=expense.amortization_end_date,
            category_id=expense.category_id,
            trip_id=expense.trip_id,
            is_expense=expense.is_expense,
        )


def _add_to_trip(
    totals: TripTotals, expense: _DecryptedExpense, period: Period
) -> None:
    totals.total_amount += expense.amount
    totals.amount_in_dates += expense.amount_in(period)
    totals.start_date = min(
        totals.start_date or expense.amortization_start_date,
        expense.amortization_start_date,
    )
    totals.end_date = max(
        totals.end_date or expense.amortization_end_date,
        expense.amortization_end_date,
    )


def _accumulated(
    expenses: list[_DecryptedExpense], period: Period, days: list[dt.date]
) -> list[Decimal]:
    """The total amortized from the start of `period` up to each of its `days`."""
    daily_amount_changes = defaultdict(Decimal)
    for expense in expenses:
        if expense.overlaps(period):
            daily_amount = expense.daily_amount()
            daily_amount_changes[expense.first_day_in(period)] += daily_amount
            daily_amount_changes[expense.last_day_in(period) + ONE_DAY] -= daily_amount
    accumulated = []
    daily_amount = total = Decimal(0)
    for day in days:
        daily_amount += daily_amount_changes[day]
        total += daily_amount
        accumulated.append(total)
    return accumulated
