from django.urls import reverse

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

    def test_update_expense_category(self):
        category = ExpenseCategoryFactory(user=self.user, for_expense=True)

        update_body = {
            "code": "updated_category",
            "name": "Updated Category",
            "for_expense": False,
        }
        res = self.client.put(self.details_url(category.id), update_body, format="json")
        self.assertEqual(res.status_code, 200)
        category.refresh_from_db()
        self.assertEqual(category.code, update_body["code"])
        self.assertEqual(category.name, update_body["name"])
        self.assertFalse(category.for_expense)

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
