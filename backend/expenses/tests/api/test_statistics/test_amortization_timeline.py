import datetime as dt
from datetime import timedelta

from expenses import date_utils
from expenses.models.user import get_hashed_password
from expenses.tests.api.api_test_case import ApiTestCase
from expenses.tests.factories.category_factories import CategoryFactory
from expenses.tests.factories.currency_factories import CurrencyFactory
from expenses.tests.factories.expense_factories import ExpenseFactory
from expenses.tests.factories.user_factories import UserFactory
from expenses.tests.factories.user_settings_factories import UserSettingsFactory
from rest_framework import status
from rest_framework.reverse import reverse


class StatisticsExpensesAmortizationTestCase(ApiTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.currency = CurrencyFactory(code="USD")
        cls.user_settings = UserSettingsFactory(
            user=cls.user, preferred_currency=cls.currency
        )
        cls.non_expense = CategoryFactory(
            user=cls.user, for_expense=False, code="income", name="salary"
        )
        cls.rent = CategoryFactory(
            user=cls.user, for_expense=True, code="rent", name="house"
        )

        cls.non_expense = [
            ExpenseFactory(
                user=cls.user,
                expense_date=date_utils.today(),
                amount=100,
                currency=cls.currency,
                category=cls.non_expense,
                amortization_start_date=date_utils.today(),
                amortization_end_date=date_utils.today() + timedelta(days=30),
                is_expense=False,
            ),
        ]

        cls.rent = [
            ExpenseFactory(
                user=cls.user,
                expense_date=date_utils.today(),
                amount=30,
                currency=cls.currency,
                category=cls.rent,
                amortization_start_date=date_utils.today(),
                amortization_end_date=date_utils.today() + timedelta(days=30),
            ),
        ]

    def url(self, start_date: dt.date, end_date: dt.date):
        return (
            f"{reverse('expenses:statistics-amortization-timeline')}"
            f"?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}"
        )

    def setUp(self):
        self.login(email=self.user.email)

    def test_statistics_expense_amortization(self):
        """
        Test the statistics expense amortization endpoint.
        """

        today = date_utils.today()
        end_month = date_utils.today() + timedelta(days=30)
        response = self.client.get(self.url(start_date=today, end_date=end_month))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class StatisticsExpenseAmortizationEncryptedTestCase(ApiTestCase):
    PASSWORD = "password"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory(password_hash=get_hashed_password(cls.PASSWORD))
        cls.currency = CurrencyFactory(code="EUR")
        cls.user_settings = UserSettingsFactory(
            user=cls.user, preferred_currency=cls.currency
        )
        cls.non_expense = CategoryFactory(
            user=cls.user, for_expense=False, code="income", name="salary"
        )
        cls.rent = CategoryFactory(
            user=cls.user, for_expense=True, code="rent", name="house"
        )

        cls.non_expense = [
            ExpenseFactory(
                user=cls.user,
                expense_date=date_utils.today(),
                amount=100,
                currency=cls.currency,
                category=cls.non_expense,
                amortization_start_date=date_utils.today(),
                amortization_end_date=date_utils.today() + timedelta(days=30),
                is_expense=False,
            ),
        ]

        cls.rent = [
            ExpenseFactory(
                user=cls.user,
                expense_date=date_utils.today(),
                amount=30,
                currency=cls.currency,
                category=cls.rent,
                amortization_start_date=date_utils.today(),
                amortization_end_date=date_utils.today() + timedelta(days=30),
            ),
        ]

    def setUp(self) -> None:
        self.login(email=self.user.email, password=self.PASSWORD)
        self.activate_encryption(self.PASSWORD)

    def url(self, start_date: dt.date, end_date: dt.date):
        return (
            f"{reverse('expenses:statistics-amortization-timeline')}"
            f"?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}"
        )

    def test_statistics_amortization_encrypted(self):
        """
        Test the statistics expense amortization endpoint for an encrypted user.
        """

        today = date_utils.today()
        end_month = date_utils.today() + timedelta(days=30)
        response = self.client.get(self.url(start_date=today, end_date=end_month))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data[0]["date"], today.isoformat())
        self.assertEqual(response.data[0]["expense_amount"], "0.97")
        self.assertEqual(response.data[0]["non_expense_amount"], "3.23")
        self.assertEqual(response.data[0]["difference"], "2.26")
