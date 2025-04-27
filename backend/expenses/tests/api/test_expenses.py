from decimal import Decimal

from rest_framework import status
from rest_framework.reverse import reverse

from expenses import date_utils
from expenses.models import Expense
from expenses.tests.api.api_test_case import ApiTestCase
from expenses.tests.factories.category_factories import (
    ExpenseCategoryFactory,
)
from expenses.tests.factories.user_factories import UserFactory


class TestCategory(ApiTestCase):
    def setUp(self):
        self.category = ExpenseCategoryFactory()
        self.url = reverse("expenses:expenses-list")
        self.today = date_utils.today()
        self.user = UserFactory()
        self.login(self.user.email)

    def test_create_expense(self):
        body = {
            "expense_date": self.today,
            "description": "test description",
            "forecast_amount": Decimal("100"),
            "actual_amount": Decimal("100"),
            "amortization_start_date": self.today,
            "amortization_end_date": self.today,
            "category": self.category.id,
            "trip": None,
            "is_expense": True,
        }
        res = self.client.post(self.url, body, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Expense.objects.count(), 1)
        new_expense = Expense.objects.get()
        for key in body:
            if key == "category":
                self.assertEqual(new_expense.category, self.category)
            else:
                self.assertEqual(
                    getattr(new_expense, key), body[key], msg=f"{key} != {body[key]}"
                )
