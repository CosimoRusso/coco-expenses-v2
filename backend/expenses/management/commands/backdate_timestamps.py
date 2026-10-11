import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass

from django.core.management import BaseCommand
from django.db.models import Min, Model, QuerySet
from expenses import date_utils
from expenses.models import (
    DollarExchangeRate,
    Expense,
    ExpenseCategory,
    PaymentMethod,
    RecurringExpense,
    Trip,
    User,
    UserSettings,
)

BATCH_SIZE = 500


@dataclass(frozen=True)
class Backdating:
    """The rows of a table to backdate, and the moment each one is backdated to."""

    rows: QuerySet
    moment_of: Callable[[Model], dt.datetime]

    @property
    def table(self) -> str:
        return self.rows.model.__name__


def _first_used(model: type[Model]) -> Backdating:
    """Noon of the earliest expense using each row; rows never used are left out."""
    rows = model.objects.annotate(first_used=Min("expenses__expense_date"))
    return Backdating(
        rows.filter(first_used__isnull=False),
        lambda row: date_utils.noon_of(row.first_used),
    )


def backdatings() -> list[Backdating]:
    """Every table to backdate. User settings come after the users they copy from."""
    return [
        Backdating(
            Expense.objects.filter(expense_date__isnull=False),
            lambda expense: date_utils.noon_of(expense.expense_date),
        ),
        Backdating(
            DollarExchangeRate.objects.all(),
            lambda rate: date_utils.noon_of(rate.date),
        ),
        Backdating(
            RecurringExpense.objects.all(),
            lambda recurring: date_utils.noon_of(recurring.start_date),
        ),
        _first_used(Trip),
        _first_used(ExpenseCategory),
        _first_used(PaymentMethod),
        Backdating(
            User.objects.filter(email_confirmed_at__isnull=False),
            lambda user: user.email_confirmed_at,
        ),
        Backdating(
            UserSettings.objects.select_related("user"),
            lambda user_settings: user_settings.user.created_at,
        ),
    ]


def backdate(backdating: Backdating) -> int:
    """Set both timestamps of each row to its moment and return how many rows they were."""
    rows = list(backdating.rows)
    for row in rows:
        row.created_at = row.updated_at = backdating.moment_of(row)
    backdating.rows.model.objects.bulk_update(
        rows, ["created_at", "updated_at"], batch_size=BATCH_SIZE
    )
    return len(rows)


class Command(BaseCommand):
    help = (
        "Set created_at and updated_at of the rows that carry or imply a date: "
        "expenses, exchange rates and recurring expenses to noon, server time, of "
        "their own date; trips, categories and payment methods to noon of their "
        "first expense; users to their e-mail confirmation; user settings to their "
        "user. Rows without such a date are left as they are."
    )

    def handle(self, *args, **options):
        for backdating in backdatings():
            count = backdate(backdating)
            self.stdout.write(f"{backdating.table}: {count} backdated")
