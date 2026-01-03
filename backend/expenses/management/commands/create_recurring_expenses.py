from django.core.management import BaseCommand
from django.db.models import QuerySet
from expenses import date_utils
from expenses.models import Expense
from expenses.models.recurring_expense import RecurringExpense
from expenses.utils.cron_parser.cron import Cron


class Command(BaseCommand):
    def handle(self, *args, **options):
        active_recurring_expenses = (
            get_active_recurring_expenses_without_expense_today()
        )
        for recurring_expense in active_recurring_expenses.iterator():
            if fires_today(recurring_expense.schedule):
                create_expense(recurring_expense)


def get_active_recurring_expenses_without_expense_today() -> QuerySet[RecurringExpense]:
    today = date_utils.today()
    return (
        RecurringExpense.objects.annotate_is_active()
        .annotate_has_expense_in_day(today)
        .filter(
            has_expense_in_day=False
        )  # To filter out recurring expenses that already have an expense for today
        .filter(is_active=True)
        .order_by("id")
    )


def fires_today(schedule: str) -> bool:
    cron = Cron(schedule)
    now = date_utils.now()
    next_run = cron.schedule(now).next()
    prev_run = cron.schedule(now).prev()
    return (
        next_run.date() == date_utils.today() or prev_run.date() == date_utils.today()
    )


def create_expense(recurring_expense: RecurringExpense):
    today = date_utils.today()
    amortization_start_date, amortization_end_date = (
        recurring_expense.calculate_amortization_dates(today)
    )
    expense = Expense(
        user=recurring_expense.user,
        expense_date=today,
        description=recurring_expense.description,
        amount=recurring_expense.amount,
        amortization_start_date=amortization_start_date,
        amortization_end_date=amortization_end_date,
        category=recurring_expense.category,
        trip=recurring_expense.trip,
        is_expense=recurring_expense.is_expense,
        currency=recurring_expense.currency,
        recurring_expense=recurring_expense,
    )
    expense.save()
