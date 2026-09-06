import datetime as dt
from datetime import timedelta

from expenses import date_utils
from expenses.models.user import get_hashed_password
from expenses.tests.api.api_test_case import ApiTestCase
from expenses.tests.factories.category_factories import CategoryFactory
from expenses.tests.factories.currency_factories import CurrencyFactory
from expenses.tests.factories.expense_factories import ExpenseFactory
from expenses.tests.factories.trip_factories import TripFactory
from expenses.tests.factories.user_factories import UserFactory
from expenses.tests.factories.user_settings_factories import UserSettingsFactory
from rest_framework import status
from rest_framework.reverse import reverse


class StatisticsExpenseCategoriesTestCase(ApiTestCase):
    PASSWORD = "password"

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(password_hash=get_hashed_password(cls.PASSWORD))
        cls.currency = CurrencyFactory(code="USD")
        cls.user_settings = UserSettingsFactory(
            user=cls.user, preferred_currency=cls.currency
        )
        cls.category_1 = CategoryFactory(
            user=cls.user, for_expense=True, code="cat1", name="Category 1"
        )
        cls.category_2 = CategoryFactory(
            user=cls.user, for_expense=True, code="cat2", name="Category 2"
        )
        cls.trip_1 = TripFactory(user=cls.user, is_active=True)
        cls.trip_2 = TripFactory(user=cls.user, is_active=True)

        cls.expenses_trip_1 = [
            ExpenseFactory(  # 25 euro a day for 4 days
                user=cls.user,
                expense_date=date_utils.today(),
                amount=100,
                currency=cls.currency,
                category=cls.category_1,
                trip=cls.trip_1,
                amortization_start_date=date_utils.today(),
                amortization_end_date=date_utils.today() + timedelta(days=3),
            ),
            ExpenseFactory(  # 20 euro a day for 5 days, forecast only
                user=cls.user,
                expense_date=None,
                amount=100,
                currency=cls.currency,
                category=cls.category_2,
                trip=cls.trip_1,
                amortization_start_date=date_utils.today(),
                amortization_end_date=date_utils.today() + timedelta(days=4),
            ),
        ]

        cls.expenses_trip_2 = [
            ExpenseFactory(  # 10 euro a day for 10 days
                user=cls.user,
                expense_date=date_utils.today(),
                amount=100,
                currency=cls.currency,
                category=cls.category_1,
                trip=cls.trip_2,
                amortization_start_date=date_utils.today() - timedelta(days=5),
                amortization_end_date=date_utils.today() + timedelta(days=4),
            ),
            ExpenseFactory(  # 10 euro a day for 1 day, old one
                user=cls.user,
                expense_date=date_utils.today() + dt.timedelta(days=10),
                amount=10,
                currency=cls.currency,
                category=cls.category_2,
                trip=cls.trip_2,
                amortization_start_date=date_utils.today() - timedelta(days=10),
                amortization_end_date=date_utils.today() - timedelta(days=10),
            ),
        ]

    def url(self, start_date: dt.date, end_date: dt.date):
        return (
            f"{reverse('expenses:statistics-trips')}"
            f"?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}"
        )

    def test_statistics_trips(self):
        """
        Test the statistics expense categories endpoint.
        """
        tests = [
            "NOT_ENCRYPTED",
            "ENCRYPTED",
        ]  # Order matters! encryption is activated after the first test without it

        for test in tests:
            with self.subTest(msg=test):
                self.login(email=self.user.email, password=self.PASSWORD)
                if test == "ENCRYPTED":
                    self.activate_encryption(password=self.PASSWORD)

                today = date_utils.today()
                tomorrow = date_utils.today() + timedelta(days=1)
                response = self.client.get(
                    self.url(start_date=today, end_date=tomorrow)
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(len(response.data), 3)  # Also includes No Trip
                # Trip 1
                self.assertEqual(response.data[0]["code"], self.trip_1.code)
                self.assertEqual(response.data[0]["name"], self.trip_1.name)
                self.assertEqual(response.data[0]["amount_in_dates"], "90.00")
                self.assertEqual(response.data[0]["total_amount"], "200.00")
                self.assertEqual(response.data[0]["price_per_day"], "40.00")
                self.assertEqual(response.data[0]["duration"], 5)
                # Trip 2
                self.assertEqual(response.data[1]["code"], self.trip_2.code)
                self.assertEqual(response.data[1]["name"], self.trip_2.name)
                self.assertEqual(response.data[1]["amount_in_dates"], "20.00")
                self.assertEqual(response.data[1]["total_amount"], "110.00")
                self.assertEqual(response.data[1]["price_per_day"], "7.33")
                self.assertEqual(response.data[1]["duration"], 15)

                # No Trip
                self.assertEqual(response.data[2]["code"], "")
                self.assertEqual(response.data[2]["name"], "No Trip")
                self.assertEqual(response.data[2]["amount_in_dates"], "0.00")
                self.assertEqual(response.data[2]["total_amount"], "0.00")
                self.assertEqual(response.data[2]["price_per_day"], None)
                self.assertEqual(response.data[2]["duration"], 0)
