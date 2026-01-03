import datetime as dt

from expenses import date_utils
from expenses.models import RecurringExpense
from expenses.tests.api.api_test_case import ApiTestCase
from expenses.tests.factories.category_factories import (
    ExpenseCategoryFactory,
    IncomeCategoryFactory,
)
from expenses.tests.factories.currency_factories import CurrencyFactory
from expenses.tests.factories.recurring_expense_factories import (
    RecurringExpenseFactory,
)
from expenses.tests.factories.trip_factories import TripFactory
from expenses.tests.factories.user_factories import UserFactory
from rest_framework import status
from rest_framework.reverse import reverse


class TestRecurringExpense(ApiTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = ExpenseCategoryFactory()
        cls.currency = CurrencyFactory(code="USD", symbol="$", display_name="Dollar")
        cls.list_url = reverse("expenses:recurring-expenses-list")
        cls.today = date_utils.today()
        cls.user = UserFactory()

    def setUp(self):
        self.login(self.user.email)

    def details_url(self, id: int) -> str:
        return reverse("expenses:recurring-expenses-detail", args=[id])

    def test_create_recurring_expense(self):
        body = {
            "start_date": self.today,
            "end_date": None,
            "amount": 100,
            "description": "test description",
            "schedule": "0 0 * * *",
            "category": self.category.id,
            "trip": None,
            "is_expense": True,
            "currency": self.currency.id,
        }
        res = self.client.post(self.list_url, body, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RecurringExpense.objects.count(), 1)
        new_recurring_expense = RecurringExpense.objects.get()
        for key in body:
            if key == "category":
                self.assertEqual(new_recurring_expense.category, self.category)
            elif key == "currency":
                self.assertEqual(new_recurring_expense.currency, self.currency)
            elif key == "end_date" and body[key] is None:
                self.assertIsNone(new_recurring_expense.end_date)
            else:
                self.assertEqual(
                    getattr(new_recurring_expense, key),
                    body[key],
                    msg=f"{key} != {body[key]}",
                )

    def test_create_recurring_expense_with_end_date(self):
        end_date = self.today + dt.timedelta(days=30)
        body = {
            "start_date": self.today,
            "end_date": end_date,
            "amount": 100,
            "description": "test description",
            "schedule": "0 0 * * *",
            "category": self.category.id,
            "trip": None,
            "is_expense": True,
            "currency": self.currency.id,
        }
        res = self.client.post(self.list_url, body, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        new_recurring_expense = RecurringExpense.objects.get()
        self.assertEqual(new_recurring_expense.end_date, end_date)

    def test_update_recurring_expense(self):
        recurring_expense = RecurringExpenseFactory(
            user=self.user, category=self.category, currency=self.currency
        )
        new_end_date = self.today + dt.timedelta(days=60)
        body = {
            "start_date": self.today,
            "end_date": new_end_date,
            "amount": 100,
            "description": "updated description",
            "schedule": "0 0 1 * *",
            "category": self.category.id,
            "trip": None,
            "is_expense": True,
            "currency": self.currency.id,
        }
        res = self.client.put(
            self.details_url(recurring_expense.id), body, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recurring_expense.refresh_from_db()
        for key in body:
            if key == "category":
                self.assertEqual(recurring_expense.category, self.category)
            elif key == "currency":
                self.assertEqual(recurring_expense.currency, self.currency)
            else:
                self.assertEqual(
                    getattr(recurring_expense, key),
                    body[key],
                    msg=f"{key} != {body[key]}",
                )

    def test_delete_recurring_expense(self):
        recurring_expense = RecurringExpenseFactory(
            user=self.user, category=self.category
        )
        res = self.client.delete(self.details_url(recurring_expense.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(
            RecurringExpense.objects.filter(pk=recurring_expense.id).first()
        )

    def test_list_recurring_expenses(self):
        recurring_expenses = [
            RecurringExpenseFactory(user=self.user, category=self.category),
            RecurringExpenseFactory(user=self.user, category=self.category),
        ]
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res = res.json()
        self.assertEqual({r["id"] for r in res}, {e.id for e in recurring_expenses})

    def test_filter_by_is_expense(self):
        expense_category = ExpenseCategoryFactory(user=self.user)
        income_category = IncomeCategoryFactory(user=self.user)
        expenses = [
            RecurringExpenseFactory(
                user=self.user, category=expense_category, is_expense=True
            ),
            RecurringExpenseFactory(
                user=self.user, category=expense_category, is_expense=True
            ),
        ]
        income_expenses = [
            RecurringExpenseFactory(
                user=self.user, category=income_category, is_expense=False
            ),
            RecurringExpenseFactory(
                user=self.user, category=income_category, is_expense=False
            ),
        ]
        res = self.client.get(self.list_url, {"is_expense": "true"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        returned_ids = {r["id"] for r in res_data}
        self.assertEqual(returned_ids, {e.id for e in expenses})
        self.assertNotIn(income_expenses[0].id, returned_ids)
        self.assertNotIn(income_expenses[1].id, returned_ids)

    def test_filter_by_category(self):
        category1 = ExpenseCategoryFactory(user=self.user)
        category2 = ExpenseCategoryFactory(user=self.user)
        recurring_expenses_category1 = [
            RecurringExpenseFactory(user=self.user, category=category1),
            RecurringExpenseFactory(user=self.user, category=category1),
        ]
        recurring_expenses_category2 = [
            RecurringExpenseFactory(user=self.user, category=category2),
            RecurringExpenseFactory(user=self.user, category=category2),
        ]
        res = self.client.get(self.list_url, {"category": category1.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        returned_ids = {r["id"] for r in res_data}
        self.assertEqual(returned_ids, {e.id for e in recurring_expenses_category1})
        self.assertNotIn(recurring_expenses_category2[0].id, returned_ids)
        self.assertNotIn(recurring_expenses_category2[1].id, returned_ids)

    def test_filter_by_trip(self):
        trip1 = TripFactory(user=self.user)
        trip2 = TripFactory(user=self.user)
        category = ExpenseCategoryFactory(user=self.user)
        recurring_expenses_trip1 = [
            RecurringExpenseFactory(user=self.user, category=category, trip=trip1),
            RecurringExpenseFactory(user=self.user, category=category, trip=trip1),
        ]
        recurring_expenses_trip2 = [
            RecurringExpenseFactory(user=self.user, category=category, trip=trip2),
            RecurringExpenseFactory(user=self.user, category=category, trip=trip2),
        ]
        recurring_expenses_no_trip = [
            RecurringExpenseFactory(user=self.user, category=category, trip=None),
            RecurringExpenseFactory(user=self.user, category=category, trip=None),
        ]
        res = self.client.get(self.list_url, {"trip": trip1.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        returned_ids = {r["id"] for r in res_data}
        self.assertEqual(returned_ids, {e.id for e in recurring_expenses_trip1})
        self.assertNotIn(recurring_expenses_trip2[0].id, returned_ids)
        self.assertNotIn(recurring_expenses_trip2[1].id, returned_ids)
        self.assertNotIn(recurring_expenses_no_trip[0].id, returned_ids)
        self.assertNotIn(recurring_expenses_no_trip[1].id, returned_ids)

    def test_filter_combinations(self):
        category1 = ExpenseCategoryFactory(user=self.user)
        category2 = ExpenseCategoryFactory(user=self.user)
        trip1 = TripFactory(user=self.user)
        trip2 = TripFactory(user=self.user)
        # Recurring expenses matching all filters
        matching_expenses = [
            RecurringExpenseFactory(
                user=self.user,
                category=category1,
                trip=trip1,
                is_expense=True,
            ),
            RecurringExpenseFactory(
                user=self.user,
                category=category1,
                trip=trip1,
                is_expense=True,
            ),
        ]
        # Recurring expenses matching only two filters
        two_filter_expenses = [
            RecurringExpenseFactory(
                user=self.user,
                category=category1,
                trip=trip1,
                is_expense=False,
            ),
            RecurringExpenseFactory(
                user=self.user,
                category=category1,
                trip=trip2,
                is_expense=True,
            ),
            RecurringExpenseFactory(
                user=self.user,
                category=category2,
                trip=trip1,
                is_expense=True,
            ),
        ]
        res = self.client.get(
            self.list_url,
            {"category": category1.id, "trip": trip1.id, "is_expense": "true"},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        returned_ids = {r["id"] for r in res_data}
        self.assertEqual(returned_ids, {e.id for e in matching_expenses})
        for expense in two_filter_expenses:
            self.assertNotIn(expense.id, returned_ids)

    def test_user_isolation(self):
        expense_category = ExpenseCategoryFactory(user=self.user)
        other_user = UserFactory()
        other_user_category = ExpenseCategoryFactory(user=other_user)
        user_recurring_expenses = [
            RecurringExpenseFactory(
                user=self.user, category=expense_category, is_expense=True
            ),
            RecurringExpenseFactory(
                user=self.user, category=expense_category, is_expense=False
            ),
        ]
        other_user_recurring_expenses = [
            RecurringExpenseFactory(
                user=other_user,
                category=other_user_category,
                is_expense=True,
            ),
            RecurringExpenseFactory(
                user=other_user,
                category=other_user_category,
                is_expense=False,
            ),
        ]
        res = self.client.get(self.list_url, {"is_expense": "true"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()
        returned_ids = {r["id"] for r in res_data}
        # Should only return the current user's recurring expense (is_expense=True)
        self.assertEqual(returned_ids, {user_recurring_expenses[0].id})
        self.assertNotIn(other_user_recurring_expenses[0].id, returned_ids)
        self.assertNotIn(other_user_recurring_expenses[1].id, returned_ids)
        self.assertNotIn(user_recurring_expenses[1].id, returned_ids)

    def test_validation_start_date_before_2000(self):
        body = {
            "start_date": dt.date(1999, 12, 31),
            "end_date": None,
            "description": "test description",
            "schedule": "0 0 * * *",
            "category": self.category.id,
            "trip": None,
            "is_expense": True,
            "currency": self.currency.id,
        }
        res = self.client.post(self.list_url, body, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Start date must be after 1 gen 2000", str(res.data))

    def test_validation_end_date_before_start_date(self):
        end_date = self.today - dt.timedelta(days=1)
        body = {
            "start_date": self.today,
            "end_date": end_date,
            "amount": 100,
            "description": "test description",
            "schedule": "0 0 * * *",
            "category": self.category.id,
            "trip": None,
            "is_expense": True,
            "currency": self.currency.id,
        }
        res = self.client.post(self.list_url, body, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Start date must be before or equal to end date", str(res.data))

    def test_validation_category_coherence(self):
        income_category = IncomeCategoryFactory(user=self.user)
        body = {
            "start_date": self.today,
            "end_date": None,
            "amount": 100,
            "description": "test description",
            "schedule": "0 0 * * *",
            "category": income_category.id,
            "trip": None,
            "is_expense": True,  # Should be False for income category
            "currency": self.currency.id,
        }
        res = self.client.post(self.list_url, body, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Category is incoherent with expense type", str(res.data))

    def test_validation_end_date_before_2000(self):
        end_date = dt.date(1999, 12, 31)
        body = {
            "start_date": self.today,
            "end_date": end_date,
            "description": "test description",
            "schedule": "0 0 * * *",
            "category": self.category.id,
            "trip": None,
            "is_expense": True,
            "currency": self.currency.id,
        }
        res = self.client.post(self.list_url, body, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("End date must be after 1 gen 2000", str(res.data))

    def test_create_recurring_expense_with_amortization_fields(self):
        """Test creating recurring expense with amortization fields"""
        body = {
            "start_date": self.today,
            "end_date": None,
            "amount": 100,
            "description": "test description",
            "schedule": "0 0 * * *",
            "category": self.category.id,
            "trip": None,
            "is_expense": True,
            "currency": self.currency.id,
            "amortization_duration": 1,
            "amortization_unit": "MONTH",
        }
        res = self.client.post(self.list_url, body, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        new_recurring_expense = RecurringExpense.objects.get()
        self.assertEqual(new_recurring_expense.amortization_duration, 1)
        self.assertEqual(new_recurring_expense.amortization_unit, "MONTH")

    def test_create_recurring_expense_with_default_amortization_fields(self):
        """Test creating recurring expense without amortization fields uses defaults"""
        body = {
            "start_date": self.today,
            "end_date": None,
            "amount": 100,
            "description": "test description",
            "schedule": "0 0 * * *",
            "category": self.category.id,
            "trip": None,
            "is_expense": True,
            "currency": self.currency.id,
        }
        res = self.client.post(self.list_url, body, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        new_recurring_expense = RecurringExpense.objects.get()
        self.assertEqual(new_recurring_expense.amortization_duration, 1)
        self.assertEqual(new_recurring_expense.amortization_unit, "DAY")

    def test_update_recurring_expense_with_amortization_fields(self):
        """Test updating recurring expense with amortization fields"""
        recurring_expense = RecurringExpenseFactory(
            user=self.user, category=self.category, currency=self.currency
        )
        body = {
            "start_date": self.today,
            "end_date": None,
            "amount": 100,
            "description": "updated description",
            "schedule": "0 0 1 * *",
            "category": self.category.id,
            "trip": None,
            "is_expense": True,
            "currency": self.currency.id,
            "amortization_duration": 2,
            "amortization_unit": "WEEK",
        }
        res = self.client.put(
            self.details_url(recurring_expense.id), body, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recurring_expense.refresh_from_db()
        self.assertEqual(recurring_expense.amortization_duration, 2)
        self.assertEqual(recurring_expense.amortization_unit, "WEEK")

    def test_validation_amortization_duration_min_value(self):
        """Test that amortization_duration must be at least 1"""
        body = {
            "start_date": self.today,
            "end_date": None,
            "amount": 100,
            "description": "test description",
            "schedule": "0 0 * * *",
            "category": self.category.id,
            "trip": None,
            "is_expense": True,
            "currency": self.currency.id,
            "amortization_duration": 0,
            "amortization_unit": "DAY",
        }
        res = self.client.post(self.list_url, body, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_validation_amortization_unit_choices(self):
        """Test that amortization_unit must be one of the valid choices"""
        body = {
            "start_date": self.today,
            "end_date": None,
            "amount": 100,
            "description": "test description",
            "schedule": "0 0 * * *",
            "category": self.category.id,
            "trip": None,
            "is_expense": True,
            "currency": self.currency.id,
            "amortization_duration": 1,
            "amortization_unit": "INVALID",
        }
        res = self.client.post(self.list_url, body, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
