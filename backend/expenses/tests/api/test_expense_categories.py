from django.urls import reverse
from rest_framework import status

from expenses.models import Settings
from expenses.tests.api.api_test_case import ApiTestCase
from expenses.tests.factories.category_factories import ExpenseCategoryFactory
from expenses.tests.factories.user_factories import UserFactory


class TestExpenses(ApiTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.list_url = reverse("expenses:expense-categories-list")

    def details_url(self, id: int) -> str:
        return reverse("expenses:expense-categories-detail", args=[id])

    def setUp(self):
        self.login(self.user.email)

    def test_create_expense_category(self):
        body = {
            "code": "test_category",
            "name": "Test Category",
            "for_expense": True,
        }
        url = reverse("expenses:expense-categories-list")
        res = self.client.post(url, body, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["code"], body["code"])
        self.assertEqual(res.data["name"], body["name"])
        self.assertTrue(res.data["for_expense"])
        self.assertTrue(res.data["is_active"])  # Default should be True

    def test_update_expense_category(self):
        category = ExpenseCategoryFactory(user=self.user, for_expense=True)

        update_body = {
            "code": "updated_category",
            "name": "Updated Category",
            "for_expense": False,
            "is_active": False,
        }
        res = self.client.put(self.details_url(category.id), update_body, format="json")
        self.assertEqual(res.status_code, 200)
        category.refresh_from_db()
        self.assertEqual(category.code, update_body["code"])
        self.assertEqual(category.name, update_body["name"])
        self.assertFalse(category.for_expense)
        self.assertFalse(category.is_active)

    def test_list_categories(self):
        other_user = UserFactory()
        other_category = ExpenseCategoryFactory(user=other_user, for_expense=True)
        categories = [
            ExpenseCategoryFactory(user=self.user, for_expense=True),
            ExpenseCategoryFactory(user=self.user, for_expense=False),
        ]

        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 2)
        for category in categories:
            self.assertIn(category.code, [cat["code"] for cat in res.data])
            self.assertIn(category.id, [cat["id"] for cat in res.data])

        self.assertNotIn(other_category.code, [cat["code"] for cat in res.data])

    def test_filter_categories_by_is_active(self):
        active_category = ExpenseCategoryFactory(user=self.user, is_active=True)
        inactive_category = ExpenseCategoryFactory(user=self.user, is_active=False)

        # Filter by active
        res = self.client.get(self.list_url, {"is_active": "true"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["id"], active_category.id)

        # Filter by inactive
        res = self.client.get(self.list_url, {"is_active": "false"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["id"], inactive_category.id)

    def test_create_category_when_limit_not_set(self):
        """Test that creation works when max_categories is not set"""
        Settings.objects.all().delete()  # Ensure no settings exist
        body = {
            "code": "test_category",
            "name": "Test Category",
            "for_expense": True,
        }
        res = self.client.post(self.list_url, body, format="json")
        self.assertEqual(res.status_code, 201)

    def test_create_category_when_limit_not_reached(self):
        """Test that creation works when limit is not reached"""
        Settings.objects.all().delete()
        Settings.objects.create(max_categories=2, max_trips=None)
        
        # Create one category (limit is 2)
        ExpenseCategoryFactory(user=self.user, code="category1", name="Category 1")
        
        body = {
            "code": "category2",
            "name": "Category 2",
            "for_expense": True,
        }
        res = self.client.post(self.list_url, body, format="json")
        self.assertEqual(res.status_code, 201)

    def test_create_category_when_limit_reached(self):
        """Test that creation fails when limit is reached"""
        Settings.objects.all().delete()
        Settings.objects.create(max_categories=2, max_trips=None)
        
        # Create two categories (reaching the limit of 2)
        ExpenseCategoryFactory(user=self.user, code="category1", name="Category 1")
        ExpenseCategoryFactory(user=self.user, code="category2", name="Category 2")
        
        body = {
            "code": "category3",
            "name": "Category 3",
            "for_expense": True,
        }
        res = self.client.post(self.list_url, body, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("Maximum number of categories (2) has been reached", str(res.data))

    def test_create_category_limit_per_user(self):
        """Test that limits are per user, not global"""
        Settings.objects.all().delete()
        Settings.objects.create(max_categories=2, max_trips=None)
        
        # Create 2 categories for self.user (reaching limit)
        ExpenseCategoryFactory(user=self.user, code="category1", name="Category 1")
        ExpenseCategoryFactory(user=self.user, code="category2", name="Category 2")
        
        # Another user should still be able to create categories
        other_user = UserFactory()
        self.login(other_user.email)
        
        body = {
            "code": "other_category1",
            "name": "Other Category 1",
            "for_expense": True,
        }
        res = self.client.post(self.list_url, body, format="json")
        self.assertEqual(res.status_code, 201)
