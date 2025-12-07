from datetime import timedelta

from rest_framework import status
from rest_framework.reverse import reverse

from expenses import date_utils
from expenses.tests.api.api_test_case import ApiTestCase
from expenses.tests.factories.category_factories import CategoryFactory
from expenses.tests.factories.expense_factories import ExpenseFactory
from expenses.tests.factories.user_factories import UserFactory
import datetime as dt


class StatisticsExpenseCategoriesTestCase(ApiTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.category_1 = CategoryFactory(
            user=cls.user, for_expense=True, code="cat1", name="Category 1"
        )
        cls.category_2 = CategoryFactory(
            user=cls.user, for_expense=True, code="cat2", name="Category 2"
        )

        cls.expenses_cat_1 = [
            ExpenseFactory(  # 25 euro a day for 4 days
                user=cls.user,
                expense_date=date_utils.today(),
                amount=100,
                actual_amount=100,
                category=cls.category_1,
                amortization_start_date=date_utils.today(),
                amortization_end_date=date_utils.today() + timedelta(days=3),
            ),
            ExpenseFactory(  # 20 euro a day for 5 days, forecast only
                user=cls.user,
                expense_date=None,
                amount=100,
                actual_amount=None,
                category=cls.category_1,
                amortization_start_date=date_utils.today(),
                amortization_end_date=date_utils.today() + timedelta(days=4),
            ),
        ]

        cls.expenses_cat_2 = [
            ExpenseFactory(  # 10 euro a day for 10 days
                user=cls.user,
                expense_date=date_utils.today(),
                amount=100,
                actual_amount=100,
                category=cls.category_2,
                amortization_start_date=date_utils.today() - timedelta(days=5),
                amortization_end_date=date_utils.today() + timedelta(days=4),
            ),
            ExpenseFactory(  # 10 euro a day for 1 day, old one
                user=cls.user,
                expense_date=date_utils.today() + dt.timedelta(days=10),
                amount=10,
                actual_amount=10,
                category=cls.category_2,
                amortization_start_date=date_utils.today() - timedelta(days=10),
                amortization_end_date=date_utils.today() - timedelta(days=10),
            ),
        ]

    def url(self, start_date: dt.date, end_date: dt.date):
        return (
            f"{reverse('expenses:statistics-expense-categories')}"
            f"?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}"
        )

    def setUp(self):
        self.login(email=self.user.email)

    def test_statistics_expense_categories(self):
        """
        Test the statistics expense categories endpoint.
        """
        today = date_utils.today()
        tomorrow = date_utils.today() + timedelta(days=1)
        response = self.client.get(self.url(start_date=today, end_date=tomorrow))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Category 1
        self.assertEqual(response.data[0]["category"]["code"], self.category_1.code)
        self.assertEqual(response.data[0]["amount"], "90.00")
        # Category 2
        self.assertEqual(response.data[1]["category"]["code"], self.category_2.code)
        self.assertEqual(response.data[1]["amount"], "20.00")


class StatisticsExpensesAmortizationTestCase(ApiTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
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
                category=cls.non_expense,
                amortization_start_date=date_utils.today(),
                amortization_end_date=date_utils.today() + timedelta(days=30),
            ),
        ]

        cls.rent = [
            ExpenseFactory(  
                user=cls.user,
                expense_date=date_utils.today(),
                amount=30,
                category=cls.rent,
                amortization_start_date=date_utils.today(),
                amortization_end_date=date_utils.today() + timedelta(days=30),
            ),
        ]

    def url(self, start_date: dt.date, end_date: dt.date):
        return (
            f"{reverse('expenses:statistics-expense-categories')}"
            f"?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}"
        )

    def setUp(self):
        self.login(email=self.user.email)

    def test_statistics_expense_categories(self):
        """
        Test the statistics expense amortization endpoint.
        """

        today = date_utils.today()
        end_month = date_utils.today() + timedelta(days=30)
        response = self.client.get(self.url(start_date=today, end_date=end_month))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 31)

        for day in range(31):
            self.assertEqual(response.data[day]["date"], today + timedelta(days=day))
            self.assertEqual(response.data[day]["amount"], "100.00")



