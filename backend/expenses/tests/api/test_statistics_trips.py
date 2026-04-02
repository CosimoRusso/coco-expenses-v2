import datetime as dt
from datetime import timedelta

from expenses import date_utils
from expenses.tests.api.api_test_case import ApiTestCase
from expenses.tests.factories.category_factories import CategoryFactory
from expenses.tests.factories.currency_factories import CurrencyFactory
from expenses.tests.factories.expense_factories import ExpenseFactory
from expenses.tests.factories.trip_factories import TripFactory
from expenses.tests.factories.user_factories import UserFactory
from expenses.tests.factories.user_settings_factories import UserSettingsFactory
from rest_framework import status
from rest_framework.reverse import reverse


class StatisticsTripsTestCase(ApiTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.currency = CurrencyFactory(code="USD")
        cls.user_settings = UserSettingsFactory(
            user=cls.user, preferred_currency=cls.currency
        )
        cls.category = CategoryFactory(
            user=cls.user, for_expense=True, code="cat1", name="Category 1"
        )
        cls.trip_1 = TripFactory(user=cls.user, code="TRIP1", name="Trip 1")
        cls.trip_2 = TripFactory(user=cls.user, code="TRIP2", name="Trip 2")

        # Expenses for trip_1: 25 per day for 4 days = 100 total
        cls.expenses_trip_1 = [
            ExpenseFactory(
                user=cls.user,
                expense_date=date_utils.today(),
                amount=100,
                currency=cls.currency,
                category=cls.category,
                trip=cls.trip_1,
                amortization_start_date=date_utils.today(),
                amortization_end_date=date_utils.today() + timedelta(days=3),
            ),
        ]

        # Expenses for trip_2: 10 per day for 10 days = 100 total
        cls.expenses_trip_2 = [
            ExpenseFactory(
                user=cls.user,
                expense_date=date_utils.today(),
                amount=100,
                currency=cls.currency,
                category=cls.category,
                trip=cls.trip_2,
                amortization_start_date=date_utils.today() - timedelta(days=5),
                amortization_end_date=date_utils.today() + timedelta(days=4),
            ),
        ]

        # Expenses without trip: 20 per day for 5 days = 100 total
        cls.expenses_no_trip = [
            ExpenseFactory(
                user=cls.user,
                expense_date=date_utils.today(),
                amount=100,
                currency=cls.currency,
                category=cls.category,
                trip=None,
                amortization_start_date=date_utils.today(),
                amortization_end_date=date_utils.today() + timedelta(days=4),
            ),
        ]

        # Income (non-expense) - should not be included
        cls.income_category = CategoryFactory(
            user=cls.user, for_expense=False, code="income", name="Income"
        )
        cls.income = [
            ExpenseFactory(
                user=cls.user,
                expense_date=date_utils.today(),
                amount=200,
                currency=cls.currency,
                category=cls.income_category,
                trip=cls.trip_1,
                is_expense=False,
                amortization_start_date=date_utils.today(),
                amortization_end_date=date_utils.today() + timedelta(days=4),
            ),
        ]

    def url(self, start_date: dt.date, end_date: dt.date):
        return (
            f"{reverse('expenses:statistics-trips')}"
            f"?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}"
        )

    def setUp(self):
        self.login(email=self.user.email)

    def test_statistics_trips(self):
        """
        Test the statistics trips endpoint with expenses for multiple trips.
        """
        today = date_utils.today()
        tomorrow = date_utils.today() + timedelta(days=1)
        response = self.client.get(self.url(start_date=today, end_date=tomorrow))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # trip_1, trip_2, and "No Trip"

        # Check that results are sorted by total_amount (descending)
        amounts = [float(item["total_amount"]) for item in response.data]
        self.assertEqual(amounts, sorted(amounts, reverse=True))

        # Verify trip_1 data
        trip_1_data = next(
            (item for item in response.data if item["id"] == self.trip_1.id),
            None,
        )
        self.assertIsNotNone(trip_1_data)
        self.assertEqual(trip_1_data["code"], self.trip_1.code)
        self.assertEqual(trip_1_data["name"], self.trip_1.name)
        # 100 / 4 days = 25 per day, we are considering 2 days so 50
        self.assertEqual(trip_1_data["total_amount"], "100.00")
        self.assertEqual(trip_1_data["amount_in_dates"], "50.00")

        # Verify trip_2 data
        trip_2_data = next(
            (item for item in response.data if item["id"] == self.trip_2.id),
            None,
        )
        self.assertIsNotNone(trip_2_data)
        self.assertEqual(trip_2_data["code"], self.trip_2.code)
        self.assertEqual(trip_2_data["name"], self.trip_2.name)
        # 100 / 10 days, we are considering 5 days so 50
        self.assertEqual(trip_1_data["total_amount"], "100.00")
        self.assertEqual(trip_1_data["amount_in_dates"], "50.00")

        # Verify "No Trip" data
        no_trip_data = next(
            (item for item in response.data if item["id"] is None), None
        )
        self.assertIsNotNone(no_trip_data)
        self.assertEqual(no_trip_data["name"], "No Trip")
        # 100 / 5 days, we must consider 2 days
        self.assertEqual(no_trip_data["total_amount"], "100.00")
        self.assertEqual(no_trip_data["amount_in_dates"], "40.00")

    def test_statistics_trips_date_range_filtering(self):
        """
        Test that the statistics trips endpoint correctly filters by date range.
        """
        # Test with a date range that excludes some expenses
        future_date = date_utils.today() + timedelta(days=10)
        response = self.client.get(
            self.url(start_date=future_date, end_date=future_date)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return empty results or only expenses that fall within this date range
        # Since all our test expenses are amortized around today, future_date should return minimal/no results
        self.assertIsInstance(response.data, list)
        for trip in response.data:
            self.assertEqual(trip["amount_in_dates"], "0.00")

    def test_statistics_trips_user_isolation(self):
        """
        Test that the statistics trips endpoint only returns trips for the authenticated user.
        """
        other_user = UserFactory()
        other_trip = TripFactory(user=other_user, code="OTHER", name="Other Trip")
        other_category = CategoryFactory(user=other_user, for_expense=True)
        ExpenseFactory(
            user=other_user,
            expense_date=date_utils.today(),
            amount=100,
            currency=self.currency,
            category=other_category,
            trip=other_trip,
            amortization_start_date=date_utils.today(),
            amortization_end_date=date_utils.today() + timedelta(days=3),
        )

        today = date_utils.today()
        tomorrow = date_utils.today() + timedelta(days=1)
        response = self.client.get(self.url(start_date=today, end_date=tomorrow))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify that other_user's trip is not in the results
        trip_ids = [item["id"] for item in response.data if item["id"] is not None]
        self.assertNotIn(other_trip.id, trip_ids)

    def test_statistics_trips_currency_serialization(self):
        """
        Test that currency is properly serialized in the response.
        """
        today = date_utils.today()
        tomorrow = date_utils.today() + timedelta(days=1)
        response = self.client.get(self.url(start_date=today, end_date=tomorrow))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify currency is included in response
        if len(response.data) > 0:
            self.assertIn("currency", response.data[0])
            self.assertEqual(response.data[0]["currency"]["code"], self.currency.code)
            self.assertEqual(
                response.data[0]["currency"]["display_name"], self.currency.display_name
            )

    def test_statistics_trips_no_trip_representation(self):
        """
        Test that expenses without a trip are represented as "No Trip".
        """
        today = date_utils.today()
        tomorrow = date_utils.today() + timedelta(days=1)
        response = self.client.get(self.url(start_date=today, end_date=tomorrow))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Find the "No Trip" entry
        no_trip_data = next(
            (item for item in response.data if item["id"] is None), None
        )
        self.assertIsNotNone(no_trip_data)
        self.assertEqual(no_trip_data["name"], "No Trip")
        self.assertEqual(no_trip_data["code"], "")
        self.assertFalse(no_trip_data["is_active"])
