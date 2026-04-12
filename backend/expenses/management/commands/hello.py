from django.core.management import BaseCommand
from django.db.models import QuerySet
from expenses import date_utils
from expenses.models import Expense
from expenses.models.recurring_expense import RecurringExpense
from expenses.utils.cron_parser.cron import Cron


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Hello world")