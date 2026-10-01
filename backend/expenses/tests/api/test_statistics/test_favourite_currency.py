import datetime as dt
from decimal import Decimal

from expenses.models import Expense
from expenses.tests.api.api_test_case import ApiTestCase
from expenses.tests.factories.category_factories import CategoryFactory
from expenses.tests.factories.currency_factories import CurrencyFactory
from expenses.tests.factories.dollar_exchange_rate_factories import (
    DollarExchangeRateFactory,
)
from expenses.tests.factories.expense_factories import ExpenseFactory
from expenses.tests.factories.user_factories import UserFactory
from expenses.tests.factories.user_settings_factories import UserSettingsFactory
from rest_framework import status
from rest_framework.reverse import reverse

DAY = dt.date(2025, 3, 10)


class StatisticsInFavouriteCurrencyTestCase(ApiTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.euro = CurrencyFactory(code="EUR")
        cls.dollar = CurrencyFactory(code="USD")
        cls.pound = CurrencyFactory(code="GBP")
        cls.user_settings = UserSettingsFactory(
            user=cls.user, preferred_currency=cls.euro
        )
        cls.food = CategoryFactory(user=cls.user, for_expense=True, code="food")
        cls.salary = CategoryFactory(user=cls.user, for_expense=False, code="salary")
        DollarExchangeRateFactory(currency=cls.euro, date=DAY, rate=Decimal("0.5"))
        DollarExchangeRateFactory(currency=cls.pound, date=DAY, rate=Decimal("0.4"))

    def setUp(self):
        self.login(email=self.user.email)

    def expense(self, **fields) -> Expense:
        defaults = {
            "user": self.user,
            "category": self.food,
            "currency": self.dollar,
            "expense_date": DAY,
            "amount": Decimal("100.00"),
            "amortization_start_date": DAY,
            "amortization_end_date": DAY,
        }
        return ExpenseFactory(**{**defaults, **fields})

    def statistics(self, name: str, start: dt.date, end: dt.date):
        url = reverse(f"expenses:statistics-{name}")
        return self.client.get(
            f"{url}?start_date={start.isoformat()}&end_date={end.isoformat()}"
        )

    def test_category_amount_is_converted_to_the_favourite_currency(self):
        self.expense(amount=Decimal("100.00"), currency=self.dollar)

        response = self.statistics("expense-categories", DAY, DAY)

        self.assertEqual(response.data[0]["amount"], "50.00")
        self.assertEqual(response.data[0]["currency"]["code"], "EUR")

    def test_reading_the_statistics_stores_the_converted_amount(self):
        expense = self.expense(amount=Decimal("100.00"), currency=self.dollar)

        self.statistics("expense-categories", DAY, DAY)

        expense.refresh_from_db()
        self.assertEqual(expense.amount_favourite_currency, Decimal("50.00"))

    def test_part_of_an_amortized_expense_in_the_period_is_rounded_once(self):
        # 50.00 EUR over 3 days: 2 days are 33.333..., not 16.67 + 16.67
        self.expense(amortization_end_date=DAY + dt.timedelta(days=2))

        response = self.statistics(
            "expense-categories", DAY, DAY + dt.timedelta(days=1)
        )

        self.assertEqual(response.data[0]["amount"], "33.33")

    def test_category_without_expenses_in_the_period_is_zero(self):
        self.expense()

        response = self.statistics(
            "expense-categories", DAY + dt.timedelta(days=1), DAY + dt.timedelta(days=1)
        )

        self.assertEqual(response.data[0]["amount"], "0.00")

    def test_income_is_not_counted_in_the_category_amounts(self):
        self.expense(category=self.salary, is_expense=False)

        response = self.statistics("expense-categories", DAY, DAY)

        self.assertEqual(response.data[0]["amount"], "0.00")

    def test_trip_totals_are_converted_to_the_favourite_currency(self):
        # 50.00 EUR over 4 days, 1 of them in the period
        self.expense(amortization_end_date=DAY + dt.timedelta(days=3))

        response = self.statistics("trips", DAY, DAY)

        no_trip = response.data[0]
        self.assertEqual(no_trip["total_amount"], "50.00")
        self.assertEqual(no_trip["amount_in_dates"], "12.50")
        self.assertEqual(no_trip["duration"], 4)
        self.assertEqual(no_trip["price_per_day"], "12.50")

    def test_timeline_accumulates_expenses_and_incomes_day_by_day(self):
        # 50.00 EUR of expenses over 3 days, 20.00 EUR of income on the second day
        self.expense(amortization_end_date=DAY + dt.timedelta(days=2))
        self.expense(
            category=self.salary,
            is_expense=False,
            amount=Decimal("40.00"),
            amortization_start_date=DAY + dt.timedelta(days=1),
            amortization_end_date=DAY + dt.timedelta(days=1),
        )

        response = self.statistics(
            "amortization-timeline", DAY, DAY + dt.timedelta(days=3)
        )

        self.assertEqual(
            response.json(),
            [
                {
                    "date": "2025-03-10",
                    "expense_amount": "16.67",
                    "non_expense_amount": "0.00",
                    "difference": "-16.67",
                },
                {
                    "date": "2025-03-11",
                    "expense_amount": "33.33",
                    "non_expense_amount": "20.00",
                    "difference": "-13.33",
                },
                {
                    "date": "2025-03-12",
                    "expense_amount": "50.00",
                    "non_expense_amount": "20.00",
                    "difference": "-30.00",
                },
                {
                    "date": "2025-03-13",
                    "expense_amount": "50.00",
                    "non_expense_amount": "20.00",
                    "difference": "-30.00",
                },
            ],
        )

    def test_timeline_starts_from_zero_at_the_start_of_the_period(self):
        # 50.00 EUR over 2 days, the first one before the period
        self.expense(
            amortization_start_date=DAY - dt.timedelta(days=1),
            amortization_end_date=DAY,
        )

        response = self.statistics("amortization-timeline", DAY, DAY)

        self.assertEqual(response.data[0]["expense_amount"], "25.00")

    def test_changing_the_favourite_currency_forgets_the_converted_amounts(self):
        expense = self.expense(amount_favourite_currency=Decimal("50.00"))

        response = self.client.put(
            reverse("expenses:user-settings-detail", args=[self.user_settings.id]),
            {"preferred_currency": self.pound.id},
            format="json",
        )

        expense.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(expense.amount_favourite_currency)

    def test_statistics_follow_a_change_of_favourite_currency(self):
        self.expense(amount=Decimal("100.00"), currency=self.dollar)
        self.statistics("expense-categories", DAY, DAY)
        self.client.put(
            reverse("expenses:user-settings-detail", args=[self.user_settings.id]),
            {"preferred_currency": self.pound.id},
            format="json",
        )

        response = self.statistics("expense-categories", DAY, DAY)

        self.assertEqual(response.data[0]["amount"], "40.00")
        self.assertEqual(response.data[0]["currency"]["code"], "GBP")

    def test_saving_the_settings_with_the_same_currency_keeps_the_amounts(self):
        expense = self.expense(amount_favourite_currency=Decimal("50.00"))

        self.client.put(
            reverse("expenses:user-settings-detail", args=[self.user_settings.id]),
            {"preferred_currency": self.euro.id},
            format="json",
        )

        expense.refresh_from_db()
        self.assertEqual(expense.amount_favourite_currency, Decimal("50.00"))

    def test_editing_an_expense_forgets_its_converted_amount(self):
        expense = self.expense(amount_favourite_currency=Decimal("50.00"))

        response = self.client.put(
            reverse("expenses:expenses-detail", args=[expense.id]),
            {
                "expense_date": DAY.isoformat(),
                "description": "Dinner",
                "amount": "30.00",
                "amortization_start_date": DAY.isoformat(),
                "amortization_end_date": DAY.isoformat(),
                "category": self.food.id,
                "is_expense": True,
                "currency": self.dollar.id,
            },
            format="json",
        )

        expense.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(expense.amount_favourite_currency)

    def test_encrypted_user_without_crypto_key_is_rejected(self):
        self.user_settings.is_encrypted = True
        self.user_settings.save()

        response = self.statistics("expense-categories", DAY, DAY)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
