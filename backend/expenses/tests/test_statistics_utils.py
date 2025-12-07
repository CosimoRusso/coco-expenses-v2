from decimal import Decimal

from django.test import SimpleTestCase

from expenses.models import Expense, ExpenseCategory
import datetime as dt

from expenses.statistics_utils import get_expenses_by_day


class StatisticsUtilsTestCase(SimpleTestCase):
    def test_get_expenses_by_day(self):
        category = ExpenseCategory(code="TEST", name="Test Category")
        today = dt.date.today()
        amortization_start_date = today
        amortization_end_date = today + dt.timedelta(days=4)
        expenses = [
            Expense(
                amortization_start_date=amortization_start_date,
                amortization_end_date=amortization_end_date,
                amount=Decimal("100.00"),
                category=category,
                description="test expense",
            )
        ]
        expenses_by_day = get_expenses_by_day(expenses)
        self.assertEqual(len(expenses_by_day.keys()), 5)
        for i in range(5):
            day = amortization_start_date + dt.timedelta(days=i)
            self.assertIn(day, expenses_by_day)
            self.assertEqual(len(expenses_by_day[day]), 1)
            expense = expenses_by_day[day][0]
            self.assertEqual(expense.amount, Decimal("20.00"))
            self.assertEqual(expense.amortization_start_date, day)
            self.assertEqual(expense.amortization_end_date, day)
