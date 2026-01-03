import datetime as dt
from decimal import Decimal
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.test import TestCase
from expenses import date_utils
from expenses.models import Expense
from expenses.tests.factories.category_factories import ExpenseCategoryFactory
from expenses.tests.factories.currency_factories import CurrencyFactory
from expenses.tests.factories.expense_factories import ExpenseFactory
from expenses.tests.factories.recurring_expense_factories import (
    RecurringExpenseFactory,
)
from expenses.tests.factories.trip_factories import TripFactory
from expenses.tests.factories.user_factories import UserFactory


class TestCreateRecurringExpensesCommand(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.category = ExpenseCategoryFactory(user=cls.user)
        cls.currency = CurrencyFactory()
        cls.trip = TripFactory(user=cls.user)
        cls.today = date_utils.today()

    def test_creates_expense_when_schedule_fires_today(self):
        """Test that expense is created when schedule fires today and no expense exists"""
        # Create a recurring expense that should fire today
        today = date_utils.today()
        recurring_expense = RecurringExpenseFactory(
            user=self.user,
            category=self.category,
            currency=self.currency,
            start_date=today - dt.timedelta(days=5),
            end_date=None,
            schedule="0 0 * * *",  # Daily at midnight
            amount=Decimal("100.00"),
        )

        initial_count = Expense.objects.count()
        call_command("create_recurring_expenses")

        # Verify expense was created
        self.assertEqual(Expense.objects.count(), initial_count + 1)
        created_expense = Expense.objects.get()
        self.assertEqual(created_expense.user, recurring_expense.user)
        self.assertEqual(created_expense.amount, recurring_expense.amount)
        self.assertEqual(created_expense.description, recurring_expense.description)
        self.assertEqual(created_expense.category, recurring_expense.category)
        self.assertEqual(created_expense.trip, recurring_expense.trip)
        self.assertEqual(created_expense.is_expense, recurring_expense.is_expense)
        self.assertEqual(created_expense.currency, recurring_expense.currency)
        self.assertEqual(created_expense.expense_date, today)
        self.assertEqual(created_expense.amortization_start_date, today)
        self.assertEqual(created_expense.amortization_end_date, today)
        self.assertEqual(created_expense.recurring_expense, recurring_expense)

    def test_does_not_create_expense_when_already_exists(self):
        """Test that expense is not created when one already exists for today"""
        # Create a recurring expense
        # Create an existing expense for today
        recurring_expense = RecurringExpenseFactory(
            user=self.user,
            category=self.category,
            currency=self.currency,
            start_date=self.today - dt.timedelta(days=5),
            end_date=None,
            schedule="0 0 * * *",
            amount=100,
            description="Test recurring expense",
        )

        ExpenseFactory(
            user=self.user,
            category=self.category,
            currency=self.currency,
            expense_date=self.today,
            recurring_expense=recurring_expense,
        )

        initial_count = Expense.objects.count()
        call_command("create_recurring_expenses")

        # Verify no new expense was created
        self.assertEqual(Expense.objects.count(), initial_count)

    @patch("expenses.management.commands.create_recurring_expenses.Cron")
    def test_does_not_create_expense_when_schedule_does_not_fire(self, mock_cron_class):
        """Test that expense is not created when schedule doesn't fire today"""

        # Create a recurring expense
        RecurringExpenseFactory(
            user=self.user,
            category=self.category,
            currency=self.currency,
            start_date=self.today - dt.timedelta(days=5),
            end_date=None,
            schedule="0 0 * * *",
        )

        # Mock Cron to return next run as tomorrow (not today) and previous run as yesterday
        mock_seeker = Mock()
        tomorrow_datetime = date_utils.now() + dt.timedelta(days=1)
        yesterday_datetime = date_utils.now() - dt.timedelta(days=1)
        mock_seeker.next.return_value = tomorrow_datetime
        mock_seeker.prev.return_value = yesterday_datetime
        mock_cron_instance = Mock()
        mock_cron_instance.schedule.return_value = mock_seeker
        mock_cron_class.return_value = mock_cron_instance

        initial_count = Expense.objects.count()
        call_command("create_recurring_expenses")

        # Verify no expense was created
        self.assertEqual(Expense.objects.count(), initial_count)

    def test_ignores_inactive_recurring_expense_before_start_date(self):
        """Test that recurring expense with start_date in future is not processed"""
        # Create a recurring expense with start_date in the future
        RecurringExpenseFactory(
            user=self.user,
            category=self.category,
            currency=self.currency,
            start_date=self.today + dt.timedelta(days=5),
            end_date=None,
            schedule="0 0 * * *",
        )

        initial_count = Expense.objects.count()
        call_command("create_recurring_expenses")

        # Verify no expense was created (recurring expense is inactive)
        self.assertEqual(Expense.objects.count(), initial_count)

    def test_ignores_inactive_recurring_expense_after_end_date(self):
        """Test that recurring expense with end_date in past is not processed"""
        # Create a recurring expense with end_date in the past
        RecurringExpenseFactory(
            user=self.user,
            category=self.category,
            currency=self.currency,
            start_date=self.today - dt.timedelta(days=10),
            end_date=self.today - dt.timedelta(days=1),
            schedule="0 0 * * *",
        )

        initial_count = Expense.objects.count()
        call_command("create_recurring_expenses")

        # Verify no expense was created (recurring expense is inactive)
        self.assertEqual(Expense.objects.count(), initial_count)

    def test_processes_active_recurring_expense_with_no_end_date(self):
        """Test that recurring expense with no end_date is processed if active"""
        # Create a recurring expense with no end_date
        recurring_expense = RecurringExpenseFactory(
            user=self.user,
            category=self.category,
            currency=self.currency,
            start_date=self.today - dt.timedelta(days=5),
            end_date=None,
            schedule="0 0 * * *",
        )

        initial_count = Expense.objects.count()
        call_command("create_recurring_expenses")

        # Verify expense was created
        self.assertEqual(Expense.objects.count(), initial_count + 1)
        created_expense = Expense.objects.get()
        self.assertEqual(created_expense.user, recurring_expense.user)

    def test_processes_multiple_matching_recurring_expenses(self):
        """Test that multiple active recurring expenses that fire today are all processed"""
        # Create multiple recurring expenses
        recurring_expense1 = RecurringExpenseFactory(
            user=self.user,
            category=self.category,
            currency=self.currency,
            start_date=self.today - dt.timedelta(days=5),
            end_date=None,
            schedule="0 0 * * *",
        )
        recurring_expense2 = RecurringExpenseFactory(
            user=self.user,
            category=self.category,
            currency=self.currency,
            start_date=self.today - dt.timedelta(days=3),
            end_date=None,
            schedule="0 0 * * *",
        )

        initial_count = Expense.objects.count()
        call_command("create_recurring_expenses")

        # Verify both expenses were created
        self.assertEqual(Expense.objects.count(), initial_count + 2)
        created_expenses = Expense.objects.all()
        self.assertEqual(
            {e.description for e in created_expenses},
            {recurring_expense1.description, recurring_expense2.description},
        )

    def test_created_expense_has_correct_fields(self):
        """Test that created expense has all correct fields from RecurringExpense"""
        # Create a recurring expense with all fields set
        recurring_expense = RecurringExpenseFactory(
            user=self.user,
            category=self.category,
            currency=self.currency,
            trip=self.trip,
            start_date=self.today - dt.timedelta(days=5),
            end_date=None,
            schedule="0 0 * * *",
            amount=Decimal("123.45"),
            description="Test recurring expense",
            is_expense=False,  # Test income case
        )

        call_command("create_recurring_expenses")

        # Verify expense was created with all correct fields
        created_expense = Expense.objects.get()
        self.assertEqual(created_expense.user, recurring_expense.user)
        self.assertEqual(created_expense.amount, recurring_expense.amount)
        self.assertEqual(created_expense.description, recurring_expense.description)
        self.assertEqual(created_expense.category, recurring_expense.category)
        self.assertEqual(created_expense.trip, recurring_expense.trip)
        self.assertEqual(created_expense.is_expense, recurring_expense.is_expense)
        self.assertEqual(created_expense.currency, recurring_expense.currency)
        self.assertEqual(created_expense.expense_date, self.today)
        self.assertEqual(created_expense.amortization_start_date, self.today)
        self.assertEqual(created_expense.amortization_end_date, self.today)

    def test_handles_empty_queryset(self):
        """Test that command completes without errors when no matching recurring expenses"""
        # Don't create any recurring expenses

        initial_count = Expense.objects.count()
        # Should not raise any exceptions
        call_command("create_recurring_expenses")

        # Verify no expenses were created
        self.assertEqual(Expense.objects.count(), initial_count)
