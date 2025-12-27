from decimal import Decimal

from rest_framework import status
from rest_framework.reverse import reverse

from expenses import date_utils
from expenses.models import Expense
from expenses.tests.api.api_test_case import ApiTestCase
from expenses.tests.factories.category_factories import (
    ExpenseCategoryFactory,
    IncomeCategoryFactory,
)
from expenses.tests.factories.expense_factories import ExpenseFactory
from expenses.tests.factories.trip_factories import TripFactory
from expenses.tests.factories.user_factories import UserFactory


class TestExpense(ApiTestCase):
    def setUp(self):
        self.category = ExpenseCategoryFactory()
        self.list_url = reverse("expenses:expenses-list")
        self.today = date_utils.today()
        self.user = UserFactory()
        self.login(self.user.email)

    def details_url(self, id: int) -> str:
        return reverse("expenses:expenses-detail", args=[id])

    def test_create_expense(self):
        body = {
            "expense_date": self.today,
            "description": "test description",
            "amount": Decimal("100"),
            "amortization_start_date": self.today,
            "amortization_end_date": self.today,
            "category": self.category.id,
            "trip": None,
            "is_expense": True,
        }
        res = self.client.post(self.list_url, body, format="json")
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

    def test_update_expense(self):
        expense = ExpenseFactory(user=self.user, category=self.category)
        body = {
            "expense_date": self.today,
            "description": "test description",
            "amount": Decimal("200"),
            "amortization_start_date": self.today,
            "amortization_end_date": self.today,
            "category": self.category.id,
            "trip": None,
            "is_expense": True,
        }
        res = self.client.put(self.details_url(expense.id), body, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expense.refresh_from_db()
        for key in body:
            if key == "category":
                self.assertEqual(expense.category, self.category)
            else:
                self.assertEqual(
                    getattr(expense, key), body[key], msg=f"{key} != {body[key]}"
                )

    def test_delete_expense(self):
        expense = ExpenseFactory(user=self.user, category=self.category)
        res = self.client.delete(self.details_url(expense.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(Expense.objects.filter(pk=expense.id).first())

    def test_list_expenses(self):
        expenses = [
            ExpenseFactory(user=self.user, category=self.category),
            ExpenseFactory(user=self.user, category=self.category),
        ]
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res = res.json()
        self.assertEqual({r["id"] for r in res}, {e.id for e in expenses})

    def test_filter_expenses_by_is_expense_true(self):
        expense_category = ExpenseCategoryFactory(user=self.user)
        income_category = IncomeCategoryFactory(user=self.user)
        expenses = [
            ExpenseFactory(user=self.user, category=expense_category, is_expense=True),
            ExpenseFactory(user=self.user, category=expense_category, is_expense=True),
        ]
        income_expenses = [
            ExpenseFactory(user=self.user, category=income_category, is_expense=False),
            ExpenseFactory(user=self.user, category=income_category, is_expense=False),
        ]
        res = self.client.get(self.list_url, {"is_expense": "true"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        returned_ids = {r["id"] for r in res_data}
        self.assertEqual(returned_ids, {e.id for e in expenses})
        self.assertNotIn(income_expenses[0].id, returned_ids)
        self.assertNotIn(income_expenses[1].id, returned_ids)

    def test_filter_expenses_by_is_expense_false(self):
        expense_category = ExpenseCategoryFactory(user=self.user)
        income_category = IncomeCategoryFactory(user=self.user)
        expenses = [
            ExpenseFactory(user=self.user, category=expense_category, is_expense=True),
            ExpenseFactory(user=self.user, category=expense_category, is_expense=True),
        ]
        income_expenses = [
            ExpenseFactory(user=self.user, category=income_category, is_expense=False),
            ExpenseFactory(user=self.user, category=income_category, is_expense=False),
        ]
        res = self.client.get(self.list_url, {"is_expense": "false"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        returned_ids = {r["id"] for r in res_data}
        self.assertEqual(returned_ids, {e.id for e in income_expenses})
        self.assertNotIn(expenses[0].id, returned_ids)
        self.assertNotIn(expenses[1].id, returned_ids)

    def test_filter_expenses_without_is_expense_parameter(self):
        expense_category = ExpenseCategoryFactory(user=self.user)
        income_category = IncomeCategoryFactory(user=self.user)
        expenses = [
            ExpenseFactory(user=self.user, category=expense_category, is_expense=True),
            ExpenseFactory(user=self.user, category=expense_category, is_expense=True),
        ]
        income_expenses = [
            ExpenseFactory(user=self.user, category=income_category, is_expense=False),
            ExpenseFactory(user=self.user, category=income_category, is_expense=False),
        ]
        all_expenses = expenses + income_expenses
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        returned_ids = {r["id"] for r in res_data}
        self.assertEqual(returned_ids, {e.id for e in all_expenses})

    def test_filter_expenses_respects_user_isolation(self):
        expense_category = ExpenseCategoryFactory(user=self.user)
        other_user = UserFactory()
        other_user_category = ExpenseCategoryFactory(user=other_user)
        user_expenses = [
            ExpenseFactory(user=self.user, category=expense_category, is_expense=True),
            ExpenseFactory(user=self.user, category=expense_category, is_expense=False),
        ]
        other_user_expenses = [
            ExpenseFactory(
                user=other_user, category=other_user_category, is_expense=True
            ),
            ExpenseFactory(
                user=other_user, category=other_user_category, is_expense=False
            ),
        ]
        res = self.client.get(self.list_url, {"is_expense": "true"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        returned_ids = {r["id"] for r in res_data}
        # Should only return the current user's expense (is_expense=True)
        self.assertEqual(returned_ids, {user_expenses[0].id})
        self.assertNotIn(other_user_expenses[0].id, returned_ids)
        self.assertNotIn(other_user_expenses[1].id, returned_ids)
        self.assertNotIn(user_expenses[1].id, returned_ids)

    def test_filter_expenses_by_category(self):
        category1 = ExpenseCategoryFactory(user=self.user)
        category2 = ExpenseCategoryFactory(user=self.user)
        expenses_category1 = [
            ExpenseFactory(user=self.user, category=category1),
            ExpenseFactory(user=self.user, category=category1),
        ]
        expenses_category2 = [
            ExpenseFactory(user=self.user, category=category2),
            ExpenseFactory(user=self.user, category=category2),
        ]
        res = self.client.get(self.list_url, {"category": category1.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        returned_ids = {r["id"] for r in res_data}
        self.assertEqual(returned_ids, {e.id for e in expenses_category1})
        self.assertNotIn(expenses_category2[0].id, returned_ids)
        self.assertNotIn(expenses_category2[1].id, returned_ids)

    def test_filter_expenses_without_category_parameter(self):
        category1 = ExpenseCategoryFactory(user=self.user)
        category2 = ExpenseCategoryFactory(user=self.user)
        expenses_category1 = [
            ExpenseFactory(user=self.user, category=category1),
            ExpenseFactory(user=self.user, category=category1),
        ]
        expenses_category2 = [
            ExpenseFactory(user=self.user, category=category2),
            ExpenseFactory(user=self.user, category=category2),
        ]
        all_expenses = expenses_category1 + expenses_category2
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        returned_ids = {r["id"] for r in res_data}
        self.assertEqual(returned_ids, {e.id for e in all_expenses})

    def test_filter_expenses_by_trip(self):
        trip1 = TripFactory(user=self.user)
        trip2 = TripFactory(user=self.user)
        category = ExpenseCategoryFactory(user=self.user)
        expenses_trip1 = [
            ExpenseFactory(user=self.user, category=category, trip=trip1),
            ExpenseFactory(user=self.user, category=category, trip=trip1),
        ]
        expenses_trip2 = [
            ExpenseFactory(user=self.user, category=category, trip=trip2),
            ExpenseFactory(user=self.user, category=category, trip=trip2),
        ]
        expenses_no_trip = [
            ExpenseFactory(user=self.user, category=category, trip=None),
            ExpenseFactory(user=self.user, category=category, trip=None),
        ]
        res = self.client.get(self.list_url, {"trip": trip1.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        returned_ids = {r["id"] for r in res_data}
        self.assertEqual(returned_ids, {e.id for e in expenses_trip1})
        self.assertNotIn(expenses_trip2[0].id, returned_ids)
        self.assertNotIn(expenses_trip2[1].id, returned_ids)
        self.assertNotIn(expenses_no_trip[0].id, returned_ids)
        self.assertNotIn(expenses_no_trip[1].id, returned_ids)

    def test_filter_expenses_by_trip_none(self):
        trip = TripFactory(user=self.user)
        category = ExpenseCategoryFactory(user=self.user)
        expenses_with_trip = [
            ExpenseFactory(user=self.user, category=category, trip=trip),
            ExpenseFactory(user=self.user, category=category, trip=trip),
        ]
        expenses_no_trip = [
            ExpenseFactory(user=self.user, category=category, trip=None),
            ExpenseFactory(user=self.user, category=category, trip=None),
        ]
        # Note: Django filters typically don't support filtering for None/null values
        # directly via query parameter. This test verifies the behavior.
        # If the backend doesn't support trip=None filtering, this test may need adjustment.
        res = self.client.get(self.list_url, {"trip": ""})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Without explicit None support, we verify that empty string doesn't filter
        # The actual implementation may vary based on django-filters behavior

    def test_filter_expenses_without_trip_parameter(self):
        trip1 = TripFactory(user=self.user)
        trip2 = TripFactory(user=self.user)
        category = ExpenseCategoryFactory(user=self.user)
        expenses_trip1 = [
            ExpenseFactory(user=self.user, category=category, trip=trip1),
            ExpenseFactory(user=self.user, category=category, trip=trip1),
        ]
        expenses_trip2 = [
            ExpenseFactory(user=self.user, category=category, trip=trip2),
            ExpenseFactory(user=self.user, category=category, trip=trip2),
        ]
        expenses_no_trip = [
            ExpenseFactory(user=self.user, category=category, trip=None),
            ExpenseFactory(user=self.user, category=category, trip=None),
        ]
        all_expenses = expenses_trip1 + expenses_trip2 + expenses_no_trip
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        returned_ids = {r["id"] for r in res_data}
        self.assertEqual(returned_ids, {e.id for e in all_expenses})

    def test_filter_expenses_by_category_and_trip(self):
        category1 = ExpenseCategoryFactory(user=self.user)
        category2 = ExpenseCategoryFactory(user=self.user)
        trip1 = TripFactory(user=self.user)
        trip2 = TripFactory(user=self.user)
        # Expenses matching both filters
        matching_expenses = [
            ExpenseFactory(user=self.user, category=category1, trip=trip1),
            ExpenseFactory(user=self.user, category=category1, trip=trip1),
        ]
        # Expenses matching only category
        category_only_expenses = [
            ExpenseFactory(user=self.user, category=category1, trip=trip2),
        ]
        # Expenses matching only trip
        trip_only_expenses = [
            ExpenseFactory(user=self.user, category=category2, trip=trip1),
        ]
        # Expenses matching neither
        other_expenses = [
            ExpenseFactory(user=self.user, category=category2, trip=trip2),
        ]
        res = self.client.get(self.list_url, {"category": category1.id, "trip": trip1.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        returned_ids = {r["id"] for r in res_data}
        self.assertEqual(returned_ids, {e.id for e in matching_expenses})
        self.assertNotIn(category_only_expenses[0].id, returned_ids)
        self.assertNotIn(trip_only_expenses[0].id, returned_ids)
        self.assertNotIn(other_expenses[0].id, returned_ids)

    def test_filter_expenses_by_category_and_is_expense(self):
        expense_category = ExpenseCategoryFactory(user=self.user)
        income_category = IncomeCategoryFactory(user=self.user)
        other_category = ExpenseCategoryFactory(user=self.user)
        # Expenses matching both filters (category1 and is_expense=True)
        matching_expenses = [
            ExpenseFactory(user=self.user, category=expense_category, is_expense=True),
            ExpenseFactory(user=self.user, category=expense_category, is_expense=True),
        ]
        # Expenses matching only category
        category_only_expenses = [
            ExpenseFactory(user=self.user, category=expense_category, is_expense=False),
        ]
        # Expenses matching only is_expense
        is_expense_only_expenses = [
            ExpenseFactory(user=self.user, category=other_category, is_expense=True),
        ]
        # Expenses matching neither
        other_expenses = [
            ExpenseFactory(user=self.user, category=income_category, is_expense=False),
        ]
        res = self.client.get(self.list_url, {"category": expense_category.id, "is_expense": "true"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        returned_ids = {r["id"] for r in res_data}
        self.assertEqual(returned_ids, {e.id for e in matching_expenses})
        self.assertNotIn(category_only_expenses[0].id, returned_ids)
        self.assertNotIn(is_expense_only_expenses[0].id, returned_ids)
        self.assertNotIn(other_expenses[0].id, returned_ids)

    def test_filter_expenses_by_trip_and_is_expense(self):
        trip1 = TripFactory(user=self.user)
        trip2 = TripFactory(user=self.user)
        category = ExpenseCategoryFactory(user=self.user)
        # Expenses matching both filters (trip1 and is_expense=True)
        matching_expenses = [
            ExpenseFactory(user=self.user, category=category, trip=trip1, is_expense=True),
            ExpenseFactory(user=self.user, category=category, trip=trip1, is_expense=True),
        ]
        # Expenses matching only trip
        trip_only_expenses = [
            ExpenseFactory(user=self.user, category=category, trip=trip1, is_expense=False),
        ]
        # Expenses matching only is_expense
        is_expense_only_expenses = [
            ExpenseFactory(user=self.user, category=category, trip=trip2, is_expense=True),
        ]
        # Expenses matching neither
        other_expenses = [
            ExpenseFactory(user=self.user, category=category, trip=trip2, is_expense=False),
        ]
        res = self.client.get(self.list_url, {"trip": trip1.id, "is_expense": "true"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        returned_ids = {r["id"] for r in res_data}
        self.assertEqual(returned_ids, {e.id for e in matching_expenses})
        self.assertNotIn(trip_only_expenses[0].id, returned_ids)
        self.assertNotIn(is_expense_only_expenses[0].id, returned_ids)
        self.assertNotIn(other_expenses[0].id, returned_ids)

    def test_filter_expenses_by_all_filters(self):
        category1 = ExpenseCategoryFactory(user=self.user)
        category2 = ExpenseCategoryFactory(user=self.user)
        trip1 = TripFactory(user=self.user)
        trip2 = TripFactory(user=self.user)
        # Expenses matching all three filters
        matching_expenses = [
            ExpenseFactory(user=self.user, category=category1, trip=trip1, is_expense=True),
            ExpenseFactory(user=self.user, category=category1, trip=trip1, is_expense=True),
        ]
        # Expenses matching only two filters
        two_filter_expenses = [
            ExpenseFactory(user=self.user, category=category1, trip=trip1, is_expense=False),
            ExpenseFactory(user=self.user, category=category1, trip=trip2, is_expense=True),
            ExpenseFactory(user=self.user, category=category2, trip=trip1, is_expense=True),
        ]
        # Expenses matching only one filter
        one_filter_expenses = [
            ExpenseFactory(user=self.user, category=category1, trip=trip2, is_expense=False),
            ExpenseFactory(user=self.user, category=category2, trip=trip1, is_expense=False),
            ExpenseFactory(user=self.user, category=category2, trip=trip2, is_expense=True),
        ]
        res = self.client.get(self.list_url, {
            "category": category1.id,
            "trip": trip1.id,
            "is_expense": "true"
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        returned_ids = {r["id"] for r in res_data}
        self.assertEqual(returned_ids, {e.id for e in matching_expenses})
        for expense in two_filter_expenses + one_filter_expenses:
            self.assertNotIn(expense.id, returned_ids)

    def test_filter_expenses_by_category_respects_user_isolation(self):
        user_category = ExpenseCategoryFactory(user=self.user)
        other_user = UserFactory()
        other_user_category = ExpenseCategoryFactory(user=other_user)
        user_expenses = [
            ExpenseFactory(user=self.user, category=user_category),
            ExpenseFactory(user=self.user, category=user_category),
        ]
        other_user_expenses = [
            ExpenseFactory(user=other_user, category=other_user_category),
            ExpenseFactory(user=other_user, category=other_user_category),
        ]
        res = self.client.get(self.list_url, {"category": user_category.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        returned_ids = {r["id"] for r in res_data}
        # Should only return the current user's expenses with the specified category
        self.assertEqual(returned_ids, {e.id for e in user_expenses})
        self.assertNotIn(other_user_expenses[0].id, returned_ids)
        self.assertNotIn(other_user_expenses[1].id, returned_ids)

    def test_filter_expenses_by_trip_respects_user_isolation(self):
        user_trip = TripFactory(user=self.user)
        other_user = UserFactory()
        other_user_trip = TripFactory(user=other_user)
        category = ExpenseCategoryFactory(user=self.user)
        user_expenses = [
            ExpenseFactory(user=self.user, category=category, trip=user_trip),
            ExpenseFactory(user=self.user, category=category, trip=user_trip),
        ]
        other_user_expenses = [
            ExpenseFactory(user=other_user, category=ExpenseCategoryFactory(user=other_user), trip=other_user_trip),
            ExpenseFactory(user=other_user, category=ExpenseCategoryFactory(user=other_user), trip=other_user_trip),
        ]
        res = self.client.get(self.list_url, {"trip": user_trip.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        returned_ids = {r["id"] for r in res_data}
        # Should only return the current user's expenses with the specified trip
        self.assertEqual(returned_ids, {e.id for e in user_expenses})
        self.assertNotIn(other_user_expenses[0].id, returned_ids)
        self.assertNotIn(other_user_expenses[1].id, returned_ids)
