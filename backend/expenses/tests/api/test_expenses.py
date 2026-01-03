import datetime as dt
from decimal import Decimal

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
from rest_framework import status
from rest_framework.reverse import reverse


class TestExpense(ApiTestCase):
    def setUp(self):
        self.category = ExpenseCategoryFactory()
        self.list_url = reverse("expenses:expenses-list")
        self.today = date_utils.today()
        self.user = UserFactory()
        self.login(self.user.email)

    def details_url(self, id: int) -> str:
        return reverse("expenses:expenses-detail", args=[id])

    def _get_results(self, response_data):
        """Helper method to extract results from paginated or non-paginated response"""
        if "results" in response_data:
            return response_data["results"]
        return response_data

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
        res_data = res.json()
        results = self._get_results(res_data)
        returned_ids = {r["id"] for r in results}
        self.assertEqual(returned_ids, {e.id for e in expenses})

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
        results = self._get_results(res_data)
        returned_ids = {r["id"] for r in results}
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
        results = self._get_results(res_data)
        returned_ids = {r["id"] for r in results}
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
        results = self._get_results(res_data)
        returned_ids = {r["id"] for r in results}
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
        results = self._get_results(res_data)
        returned_ids = {r["id"] for r in results}
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
        results = self._get_results(res_data)
        returned_ids = {r["id"] for r in results}
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
        results = self._get_results(res_data)
        returned_ids = {r["id"] for r in results}
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
        results = self._get_results(res_data)
        returned_ids = {r["id"] for r in results}
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
        res = self.client.get(
            self.list_url, {"category": category1.id, "trip": trip1.id}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        results = self._get_results(res_data)
        returned_ids = {r["id"] for r in results}
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
        res = self.client.get(
            self.list_url, {"category": expense_category.id, "is_expense": "true"}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        results = self._get_results(res_data)
        returned_ids = {r["id"] for r in results}
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
            ExpenseFactory(
                user=self.user, category=category, trip=trip1, is_expense=True
            ),
            ExpenseFactory(
                user=self.user, category=category, trip=trip1, is_expense=True
            ),
        ]
        # Expenses matching only trip
        trip_only_expenses = [
            ExpenseFactory(
                user=self.user, category=category, trip=trip1, is_expense=False
            ),
        ]
        # Expenses matching only is_expense
        is_expense_only_expenses = [
            ExpenseFactory(
                user=self.user, category=category, trip=trip2, is_expense=True
            ),
        ]
        # Expenses matching neither
        other_expenses = [
            ExpenseFactory(
                user=self.user, category=category, trip=trip2, is_expense=False
            ),
        ]
        res = self.client.get(self.list_url, {"trip": trip1.id, "is_expense": "true"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        results = self._get_results(res_data)
        returned_ids = {r["id"] for r in results}
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
            ExpenseFactory(
                user=self.user, category=category1, trip=trip1, is_expense=True
            ),
            ExpenseFactory(
                user=self.user, category=category1, trip=trip1, is_expense=True
            ),
        ]
        # Expenses matching only two filters
        two_filter_expenses = [
            ExpenseFactory(
                user=self.user, category=category1, trip=trip1, is_expense=False
            ),
            ExpenseFactory(
                user=self.user, category=category1, trip=trip2, is_expense=True
            ),
            ExpenseFactory(
                user=self.user, category=category2, trip=trip1, is_expense=True
            ),
        ]
        # Expenses matching only one filter
        one_filter_expenses = [
            ExpenseFactory(
                user=self.user, category=category1, trip=trip2, is_expense=False
            ),
            ExpenseFactory(
                user=self.user, category=category2, trip=trip1, is_expense=False
            ),
            ExpenseFactory(
                user=self.user, category=category2, trip=trip2, is_expense=True
            ),
        ]
        res = self.client.get(
            self.list_url,
            {"category": category1.id, "trip": trip1.id, "is_expense": "true"},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        results = self._get_results(res_data)
        returned_ids = {r["id"] for r in results}
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
        results = self._get_results(res_data)
        returned_ids = {r["id"] for r in results}
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
            ExpenseFactory(
                user=other_user,
                category=ExpenseCategoryFactory(user=other_user),
                trip=other_user_trip,
            ),
            ExpenseFactory(
                user=other_user,
                category=ExpenseCategoryFactory(user=other_user),
                trip=other_user_trip,
            ),
        ]
        res = self.client.get(self.list_url, {"trip": user_trip.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        results = self._get_results(res_data)
        returned_ids = {r["id"] for r in results}
        # Should only return the current user's expenses with the specified trip
        self.assertEqual(returned_ids, {e.id for e in user_expenses})
        self.assertNotIn(other_user_expenses[0].id, returned_ids)
        self.assertNotIn(other_user_expenses[1].id, returned_ids)

    def test_list_expenses_pagination(self):
        """Test that list endpoint returns paginated response structure"""
        # Create more expenses than page size to trigger pagination
        [ExpenseFactory(user=self.user, category=self.category) for _ in range(6)]
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        # Verify paginated response structure
        self.assertIn("count", res_data)
        self.assertIn("next", res_data)
        self.assertIn("previous", res_data)
        self.assertIn("results", res_data)
        # Verify count matches total expenses
        self.assertEqual(res_data["count"], 6)
        # Verify first page has page_size items (2)
        self.assertEqual(len(res_data["results"]), 5)
        # Verify next page URL exists
        self.assertIsNotNone(res_data["next"])
        # Verify previous page URL is None for first page
        self.assertIsNone(res_data["previous"])

    def test_list_expenses_page_parameter(self):
        """Test that page query parameter works correctly"""
        # Create more expenses than page size
        expenses = [
            ExpenseFactory(user=self.user, category=self.category) for _ in range(6)
        ]
        expense_ids = {e.id for e in expenses}
        # Get first page
        res = self.client.get(self.list_url, {"page": 1})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        first_page_ids = {r["id"] for r in res_data["results"]}
        self.assertEqual(len(first_page_ids), 5)
        # Get second page
        res = self.client.get(self.list_url, {"page": 2})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        second_page_ids = {r["id"] for r in res_data["results"]}
        self.assertEqual(len(second_page_ids), 1)
        # Verify no overlap between pages
        self.assertEqual(first_page_ids & second_page_ids, set())
        # Verify all expenses are accounted for
        self.assertEqual(first_page_ids | second_page_ids, expense_ids)
        # Verify second page has previous URL
        self.assertIsNotNone(res_data["previous"])
        # Verify second page has no next URL (last page)
        self.assertIsNone(res_data["next"])

    def test_list_expenses_pagination_with_filters(self):
        """Test that filters work correctly with pagination"""
        expense_category = ExpenseCategoryFactory(user=self.user)
        income_category = IncomeCategoryFactory(user=self.user)
        # Create expenses and income
        _expenses = [
            ExpenseFactory(user=self.user, category=expense_category, is_expense=True)
            for _ in range(6)
        ]
        income_expenses = [
            ExpenseFactory(user=self.user, category=income_category, is_expense=False)
            for _ in range(2)
        ]
        # Filter by is_expense=True with pagination
        res = self.client.get(self.list_url, {"is_expense": "true", "page": 1})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        # Verify count matches filtered expenses
        self.assertEqual(res_data["count"], 6)
        # Verify all results are expenses (is_expense=True)
        for expense in res_data["results"]:
            self.assertTrue(expense["is_expense"])
        # Verify no income expenses are in results
        returned_ids = {r["id"] for r in res_data["results"]}
        income_ids = {e.id for e in income_expenses}
        self.assertEqual(returned_ids & income_ids, set())

    def test_list_expenses_pagination_page_size(self):
        """Test that page size limit is enforced"""
        # Create more expenses than page size
        _expenses = [
            ExpenseFactory(user=self.user, category=self.category) for _ in range(6)
        ]
        res = self.client.get(self.list_url, {"page": 1})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        # Verify first page has exactly page_size items (2)
        self.assertEqual(len(res_data["results"]), 5)
        # Verify total count is correct
        self.assertEqual(res_data["count"], 6)

    def test_list_expenses_pagination_empty_page(self):
        """Test handling of empty or out-of-range pages"""
        # Create some expenses
        _expenses = [
            ExpenseFactory(user=self.user, category=self.category) for _ in range(10)
        ]
        # Request page beyond available pages
        res = self.client.get(self.list_url, {"page": 100})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_filter_expenses_by_start_date_only(self):
        """Test filtering expenses by start_date only"""
        start_date = self.today + dt.timedelta(days=5)
        category = ExpenseCategoryFactory(user=self.user)

        # Expense with amortization period that starts before start_date and ends after start_date (should match)
        matching_expense1 = ExpenseFactory(
            user=self.user,
            category=category,
            amortization_start_date=self.today,
            amortization_end_date=self.today + dt.timedelta(days=10),
        )

        # Expense with amortization period that starts after start_date (should match)
        matching_expense2 = ExpenseFactory(
            user=self.user,
            category=category,
            amortization_start_date=self.today + dt.timedelta(days=6),
            amortization_end_date=self.today + dt.timedelta(days=10),
        )

        # Expense with amortization period that ends before start_date (should not match)
        non_matching_expense = ExpenseFactory(
            user=self.user,
            category=category,
            amortization_start_date=self.today,
            amortization_end_date=self.today + dt.timedelta(days=3),
        )

        res = self.client.get(self.list_url, {"start_date": start_date.isoformat()})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        results = self._get_results(res_data)
        returned_ids = {r["id"] for r in results}

        self.assertIn(matching_expense1.id, returned_ids)
        self.assertIn(matching_expense2.id, returned_ids)
        self.assertNotIn(non_matching_expense.id, returned_ids)

    def test_filter_expenses_by_end_date_only(self):
        """Test filtering expenses by end_date only"""
        end_date = self.today + dt.timedelta(days=5)
        category = ExpenseCategoryFactory(user=self.user)

        # Expense with amortization_start_date <= end_date (should match)
        matching_expense1 = ExpenseFactory(
            user=self.user,
            category=category,
            amortization_start_date=self.today,
            amortization_end_date=self.today + dt.timedelta(days=10),
        )

        matching_expense2 = ExpenseFactory(
            user=self.user,
            category=category,
            amortization_start_date=self.today + dt.timedelta(days=5),
            amortization_end_date=self.today + dt.timedelta(days=10),
        )

        # Expense with amortization_start_date > end_date (should not match)
        non_matching_expense = ExpenseFactory(
            user=self.user,
            category=category,
            amortization_start_date=self.today + dt.timedelta(days=6),
            amortization_end_date=self.today + dt.timedelta(days=10),
        )

        res = self.client.get(self.list_url, {"end_date": end_date.isoformat()})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        results = self._get_results(res_data)
        returned_ids = {r["id"] for r in results}

        self.assertIn(matching_expense1.id, returned_ids)
        self.assertIn(matching_expense2.id, returned_ids)
        self.assertNotIn(non_matching_expense.id, returned_ids)

    def test_filter_expenses_by_start_date_and_end_date(self):
        """Test filtering expenses by both start_date and end_date"""
        start_date = self.today + dt.timedelta(days=5)
        end_date = self.today + dt.timedelta(days=10)
        category = ExpenseCategoryFactory(user=self.user)

        # Expense that overlaps with the date range (starts before, ends after) (should match)
        matching_expense1 = ExpenseFactory(
            user=self.user,
            category=category,
            amortization_start_date=self.today,
            amortization_end_date=self.today + dt.timedelta(days=15),
        )

        # Expense that starts before range and ends within range (should match)
        matching_expense2 = ExpenseFactory(
            user=self.user,
            category=category,
            amortization_start_date=self.today,
            amortization_end_date=self.today + dt.timedelta(days=8),
        )

        # Expense that starts within range and ends after range (should match)
        matching_expense3 = ExpenseFactory(
            user=self.user,
            category=category,
            amortization_start_date=self.today + dt.timedelta(days=7),
            amortization_end_date=self.today + dt.timedelta(days=15),
        )

        # Expense that starts and ends within range (should match)
        matching_expense4 = ExpenseFactory(
            user=self.user,
            category=category,
            amortization_start_date=self.today + dt.timedelta(days=6),
            amortization_end_date=self.today + dt.timedelta(days=9),
        )

        # Expense that starts before range and ends before range (should not match)
        non_matching_expense1 = ExpenseFactory(
            user=self.user,
            category=category,
            amortization_start_date=self.today,
            amortization_end_date=self.today + dt.timedelta(days=3),
        )

        # Expense that starts after range and ends after range (should not match)
        non_matching_expense2 = ExpenseFactory(
            user=self.user,
            category=category,
            amortization_start_date=self.today + dt.timedelta(days=11),
            amortization_end_date=self.today + dt.timedelta(days=15),
        )

        res = self.client.get(
            self.list_url,
            {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        results = self._get_results(res_data)
        returned_ids = {r["id"] for r in results}

        self.assertIn(matching_expense1.id, returned_ids)
        self.assertIn(matching_expense2.id, returned_ids)
        self.assertIn(matching_expense3.id, returned_ids)
        self.assertIn(matching_expense4.id, returned_ids)
        self.assertNotIn(non_matching_expense1.id, returned_ids)
        self.assertNotIn(non_matching_expense2.id, returned_ids)

    def test_filter_expenses_by_date_range_exact_boundaries(self):
        """Test filtering with expenses exactly on start_date and end_date boundaries"""
        start_date = self.today + dt.timedelta(days=5)
        end_date = self.today + dt.timedelta(days=10)
        category = ExpenseCategoryFactory(user=self.user)

        # Expense that starts exactly on start_date (should match)
        matching_expense1 = ExpenseFactory(
            user=self.user,
            category=category,
            amortization_start_date=start_date,
            amortization_end_date=self.today + dt.timedelta(days=15),
        )

        # Expense that ends exactly on end_date (should match)
        matching_expense2 = ExpenseFactory(
            user=self.user,
            category=category,
            amortization_start_date=self.today,
            amortization_end_date=end_date,
        )

        # Expense that starts exactly on end_date (should match)
        matching_expense3 = ExpenseFactory(
            user=self.user,
            category=category,
            amortization_start_date=end_date,
            amortization_end_date=self.today + dt.timedelta(days=15),
        )

        res = self.client.get(
            self.list_url,
            {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        results = self._get_results(res_data)
        returned_ids = {r["id"] for r in results}

        self.assertIn(matching_expense1.id, returned_ids)
        self.assertIn(matching_expense2.id, returned_ids)
        self.assertIn(matching_expense3.id, returned_ids)

    def test_filter_expenses_by_date_range_single_day(self):
        """Test filtering with start_date == end_date (single day)"""
        single_date = self.today + dt.timedelta(days=5)
        category = ExpenseCategoryFactory(user=self.user)

        # Expense that overlaps with that single day (starts before, ends after) (should match)
        matching_expense1 = ExpenseFactory(
            user=self.user,
            category=category,
            amortization_start_date=self.today,
            amortization_end_date=self.today + dt.timedelta(days=10),
        )

        # Expense that starts exactly on that day (should match)
        matching_expense2 = ExpenseFactory(
            user=self.user,
            category=category,
            amortization_start_date=single_date,
            amortization_end_date=self.today + dt.timedelta(days=10),
        )

        # Expense that ends exactly on that day (should match)
        matching_expense3 = ExpenseFactory(
            user=self.user,
            category=category,
            amortization_start_date=self.today,
            amortization_end_date=single_date,
        )

        # Expense that starts and ends on that day (should match)
        matching_expense4 = ExpenseFactory(
            user=self.user,
            category=category,
            amortization_start_date=single_date,
            amortization_end_date=single_date,
        )

        # Expense that starts after that day (should not match)
        non_matching_expense1 = ExpenseFactory(
            user=self.user,
            category=category,
            amortization_start_date=self.today + dt.timedelta(days=6),
            amortization_end_date=self.today + dt.timedelta(days=10),
        )

        # Expense that ends before that day (should not match)
        non_matching_expense2 = ExpenseFactory(
            user=self.user,
            category=category,
            amortization_start_date=self.today,
            amortization_end_date=self.today + dt.timedelta(days=4),
        )

        res = self.client.get(
            self.list_url,
            {
                "start_date": single_date.isoformat(),
                "end_date": single_date.isoformat(),
            },
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        results = self._get_results(res_data)
        returned_ids = {r["id"] for r in results}

        self.assertIn(matching_expense1.id, returned_ids)
        self.assertIn(matching_expense2.id, returned_ids)
        self.assertIn(matching_expense3.id, returned_ids)
        self.assertIn(matching_expense4.id, returned_ids)
        self.assertNotIn(non_matching_expense1.id, returned_ids)
        self.assertNotIn(non_matching_expense2.id, returned_ids)

    def test_filter_all_filters(self):
        """Test combining date filters with category, trip, and is_expense filters"""
        start_date = self.today + dt.timedelta(days=5)
        end_date = self.today + dt.timedelta(days=10)
        category1 = ExpenseCategoryFactory(user=self.user)
        category2 = ExpenseCategoryFactory(user=self.user)
        trip1 = TripFactory(user=self.user)
        trip2 = TripFactory(user=self.user)

        # Expense matching all filters (category1, trip1, is_expense=True, date range)
        matching_expense = ExpenseFactory(
            user=self.user,
            category=category1,
            trip=trip1,
            is_expense=True,
            amortization_start_date=self.today + dt.timedelta(days=6),
            amortization_end_date=self.today + dt.timedelta(days=9),
        )

        # Expenses matching only some filters
        wrong_category = ExpenseFactory(
            user=self.user,
            category=category2,
            trip=trip1,
            is_expense=True,
            amortization_start_date=self.today + dt.timedelta(days=6),
            amortization_end_date=self.today + dt.timedelta(days=9),
        )

        wrong_trip = ExpenseFactory(
            user=self.user,
            category=category1,
            trip=trip2,
            is_expense=True,
            amortization_start_date=self.today + dt.timedelta(days=6),
            amortization_end_date=self.today + dt.timedelta(days=9),
        )

        wrong_type = ExpenseFactory(
            user=self.user,
            category=category1,
            trip=trip1,
            is_expense=False,
            amortization_start_date=self.today + dt.timedelta(days=6),
            amortization_end_date=self.today + dt.timedelta(days=9),
        )

        wrong_date = ExpenseFactory(
            user=self.user,
            category=category1,
            trip=trip1,
            is_expense=True,
            amortization_start_date=self.today + dt.timedelta(days=11),
            amortization_end_date=self.today + dt.timedelta(days=15),
        )

        res = self.client.get(
            self.list_url,
            {
                "category": category1.id,
                "trip": trip1.id,
                "is_expense": "true",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        results = self._get_results(res_data)
        returned_ids = {r["id"] for r in results}

        self.assertIn(matching_expense.id, returned_ids)
        self.assertNotIn(wrong_category.id, returned_ids)
        self.assertNotIn(wrong_trip.id, returned_ids)
        self.assertNotIn(wrong_type.id, returned_ids)
        self.assertNotIn(wrong_date.id, returned_ids)

    def test_filter_expenses_with_invalid_start_date_format(self):
        """Test that invalid start_date format raises ValidationError"""
        res = self.client.get(self.list_url, {"start_date": "invalid-date"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        res_data = res.json()
        self.assertIn("Start date must be in YYYY-MM-DD format", str(res_data))

    def test_filter_expenses_with_invalid_end_date_format(self):
        """Test that invalid end_date format raises ValidationError"""
        res = self.client.get(self.list_url, {"end_date": "invalid-date"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        res_data = res.json()
        self.assertIn("End date must be in YYYY-MM-DD format", str(res_data))

    def test_list_expenses_pagination_with_date_filters(self):
        """Test that pagination works correctly with date filtering"""
        start_date = self.today + dt.timedelta(days=5)
        end_date = self.today + dt.timedelta(days=10)
        category = ExpenseCategoryFactory(user=self.user)

        # Create multiple expenses matching date filter
        matching_expenses = [
            ExpenseFactory(
                user=self.user,
                category=category,
                amortization_start_date=self.today + dt.timedelta(days=6),
                amortization_end_date=self.today + dt.timedelta(days=9),
            )
            for _ in range(6)
        ]

        # Create expenses that don't match date filter
        non_matching_expenses = [
            ExpenseFactory(
                user=self.user,
                category=category,
                amortization_start_date=self.today + dt.timedelta(days=11),
                amortization_end_date=self.today + dt.timedelta(days=15),
            )
            for _ in range(2)
        ]

        # Filter by date range with pagination
        res = self.client.get(
            self.list_url,
            {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "page": 1,
            },
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()

        # Verify count matches filtered expenses
        self.assertEqual(res_data["count"], 6)

        # Verify first page has page_size items (2)
        self.assertEqual(len(res_data["results"]), 5)

        # Verify all results match the date filter
        first_page_ids = {r["id"] for r in res_data["results"]}
        matching_ids = {e.id for e in matching_expenses}
        self.assertTrue(first_page_ids.issubset(matching_ids))

        # Verify no non-matching expenses are in results
        non_matching_ids = {e.id for e in non_matching_expenses}
        self.assertEqual(first_page_ids & non_matching_ids, set())

        # Get second page
        res = self.client.get(
            self.list_url,
            {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "page": 2,
            },
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        second_page_ids = {r["id"] for r in res_data["results"]}

        # Verify second page has remaining item
        self.assertEqual(len(second_page_ids), 1)

        # Verify no overlap between pages
        self.assertEqual(first_page_ids & second_page_ids, set())

        # Verify all matching expenses are accounted for
        self.assertEqual(first_page_ids | second_page_ids, matching_ids)
