import datetime as dt
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from expenses.models import UserSettings
from expenses.tests.factories.category_factories import ExpenseCategoryFactory
from expenses.tests.factories.currency_factories import CurrencyFactory
from expenses.tests.factories.dollar_exchange_rate_factories import (
    DollarExchangeRateFactory,
)
from expenses.tests.factories.expense_factories import ExpenseFactory
from expenses.tests.factories.payment_method_factories import PaymentMethodFactory
from expenses.tests.factories.recurring_expense_factories import (
    RecurringExpenseFactory,
)
from expenses.tests.factories.trip_factories import TripFactory
from expenses.tests.factories.user_factories import UserFactory

THIRD_OF_MARCH = dt.date(2024, 3, 3)
FIFTH_OF_MARCH = dt.date(2024, 3, 5)
NOON_OF_3_MARCH = dt.datetime(2024, 3, 3, 12, 0, tzinfo=dt.timezone.utc)
CONFIRMED_AT = dt.datetime(2023, 7, 9, 18, 30, tzinfo=dt.timezone.utc)


class BackdateTimestampsTestCase(TestCase):
    def run_command(self) -> str:
        out = StringIO()
        call_command("backdate_timestamps", stdout=out)
        return out.getvalue()

    def backdated(self, row):
        """Run the command and return the timestamps `row` ends up with."""
        self.run_command()
        row.refresh_from_db()
        return (row.created_at, row.updated_at)


class TestBackdateByOwnDate(BackdateTimestampsTestCase):
    def test_expense_takes_noon_of_its_date(self):
        expense = ExpenseFactory(expense_date=THIRD_OF_MARCH)

        timestamps = self.backdated(expense)

        self.assertEqual(timestamps, (NOON_OF_3_MARCH, NOON_OF_3_MARCH))

    def test_expense_without_a_date_keeps_its_timestamps(self):
        expense = ExpenseFactory(expense_date=None)
        created_at = expense.created_at

        timestamps = self.backdated(expense)

        self.assertEqual(timestamps[0], created_at)

    def test_exchange_rate_takes_noon_of_its_date(self):
        rate = DollarExchangeRateFactory(
            currency=CurrencyFactory(), date=THIRD_OF_MARCH, rate="0.85"
        )

        timestamps = self.backdated(rate)

        self.assertEqual(timestamps, (NOON_OF_3_MARCH, NOON_OF_3_MARCH))

    def test_recurring_expense_takes_noon_of_its_start_date(self):
        recurring_expense = RecurringExpenseFactory(start_date=THIRD_OF_MARCH)

        timestamps = self.backdated(recurring_expense)

        self.assertEqual(timestamps, (NOON_OF_3_MARCH, NOON_OF_3_MARCH))


class TestBackdateByFirstUsage(BackdateTimestampsTestCase):
    def test_trip_takes_noon_of_its_earliest_expense(self):
        trip = TripFactory()
        ExpenseFactory(trip=trip, expense_date=FIFTH_OF_MARCH)
        ExpenseFactory(trip=trip, expense_date=THIRD_OF_MARCH)

        timestamps = self.backdated(trip)

        self.assertEqual(timestamps, (NOON_OF_3_MARCH, NOON_OF_3_MARCH))

    def test_category_takes_noon_of_its_earliest_expense(self):
        category = ExpenseCategoryFactory()
        ExpenseFactory(category=category, expense_date=FIFTH_OF_MARCH)
        ExpenseFactory(category=category, expense_date=THIRD_OF_MARCH)

        timestamps = self.backdated(category)

        self.assertEqual(timestamps, (NOON_OF_3_MARCH, NOON_OF_3_MARCH))

    def test_payment_method_takes_noon_of_its_earliest_expense(self):
        payment_method = PaymentMethodFactory()
        ExpenseFactory(payment_method=payment_method, expense_date=FIFTH_OF_MARCH)
        ExpenseFactory(payment_method=payment_method, expense_date=THIRD_OF_MARCH)

        timestamps = self.backdated(payment_method)

        self.assertEqual(timestamps, (NOON_OF_3_MARCH, NOON_OF_3_MARCH))

    def test_trip_never_used_keeps_its_timestamps(self):
        trip = TripFactory()
        created_at = trip.created_at

        timestamps = self.backdated(trip)

        self.assertEqual(timestamps[0], created_at)


class TestBackdateUsers(BackdateTimestampsTestCase):
    def test_user_takes_the_moment_they_confirmed_their_email(self):
        user = UserFactory(email_confirmed_at=CONFIRMED_AT)

        timestamps = self.backdated(user)

        self.assertEqual(timestamps, (CONFIRMED_AT, CONFIRMED_AT))

    def test_unconfirmed_user_keeps_their_timestamps(self):
        user = UserFactory(email_confirmed_at=None)
        created_at = user.created_at

        timestamps = self.backdated(user)

        self.assertEqual(timestamps[0], created_at)

    def test_user_settings_take_the_backdated_timestamps_of_their_user(self):
        user = UserFactory(email_confirmed_at=CONFIRMED_AT)
        user_settings = UserSettings.objects.create(user=user)

        timestamps = self.backdated(user_settings)

        self.assertEqual(timestamps, (CONFIRMED_AT, CONFIRMED_AT))


class TestBackdateReport(BackdateTimestampsTestCase):
    def test_reports_how_many_rows_of_each_table_were_backdated(self):
        user = UserFactory(email_confirmed_at=None)
        category = ExpenseCategoryFactory(user=user)
        ExpenseFactory(user=user, category=category, expense_date=THIRD_OF_MARCH)

        output = self.run_command()

        self.assertEqual(
            output,
            "Expense: 1 backdated\n"
            "DollarExchangeRate: 0 backdated\n"
            "RecurringExpense: 0 backdated\n"
            "Trip: 0 backdated\n"
            "ExpenseCategory: 1 backdated\n"
            "PaymentMethod: 0 backdated\n"
            "User: 0 backdated\n"
            "UserSettings: 0 backdated\n",
        )
