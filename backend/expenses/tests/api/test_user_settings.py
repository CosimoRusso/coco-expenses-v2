from django.urls import reverse
from expenses.models.currency import Currency
from expenses.models.user_settings import UserSettings
from expenses.tests.api.api_test_case import ApiTestCase
from expenses.tests.factories.category_factories import CategoryFactory
from expenses.tests.factories.currency_factories import CurrencyFactory
from expenses.tests.factories.expense_factories import ExpenseFactory
from expenses.tests.factories.trip_factories import TripFactory
from expenses.tests.factories.user_factories import UserFactory
from expenses.utils.encryption.encryption import decrypt_text_with_password
from rest_framework import status as http_status


class TestUserSettings(ApiTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.list_url = reverse("expenses:user-settings-list")
        cls.currency = CurrencyFactory()
        cls.trip = TripFactory()

    def setUp(self):
        self.login(self.user.email)

    def details_url(self, id: int) -> str:
        return reverse("expenses:user-settings-detail", args=[id])

    def test_cannot_create_user_settings(self):
        body = {"preferred_currency": 1, "active_trip": 1}
        res = self.client.post(self.list_url, body, format="json")
        self.assertEqual(res.status_code, http_status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_settings(self):
        user_settings = UserSettings.objects.get(user=self.user)
        body = {"preferred_currency": self.currency.id, "active_trip": self.trip.id}
        res = self.client.patch(self.details_url(user_settings.id), body, format="json")
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)
        user_settings.refresh_from_db()
        self.assertEqual(user_settings.preferred_currency, self.currency)
        self.assertEqual(user_settings.active_trip, self.trip)

    def test_update_cannot_activate_encryption(self):
        user_settings = UserSettings.objects.get(user=self.user)
        body = {"is_encrypted": True}
        res = self.client.patch(self.details_url(user_settings.id), body, format="json")
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)
        user_settings.refresh_from_db()
        self.assertFalse(user_settings.is_encrypted)

    def test_update_cannot_deactivate_encryption(self):
        user_settings = UserSettings.objects.get(user=self.user)
        user_settings.is_encrypted = True
        user_settings.save(update_fields=["is_encrypted"])
        body = {"is_encrypted": False}
        res = self.client.patch(self.details_url(user_settings.id), body, format="json")
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)
        user_settings.refresh_from_db()
        self.assertTrue(user_settings.is_encrypted)

    def test_get_user_settings(self):
        user_settings = UserSettings.objects.get(user=self.user)
        res = self.client.get(self.details_url(user_settings.id))
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)
        self.assertEqual(
            res.data["preferred_currency"], user_settings.preferred_currency_id
        )
        self.assertEqual(res.data["active_trip"], user_settings.active_trip_id)
        self.assertEqual(res.data["is_encrypted"], user_settings.is_encrypted)

    def cannot_get_user_settings_for_other_user(self):
        other_user = UserFactory()
        other_user_settings = UserSettings.objects.get(user=other_user)
        res = self.client.get(self.details_url(other_user_settings.id))
        self.assertEqual(res.status_code, http_status.HTTP_404_NOT_FOUND)

    def test_self_user_settings(self):
        res = self.client.get(reverse("expenses:user-settings-self"))
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)
        res = res.json()
        user_settings = UserSettings.objects.get(user=self.user)
        self.assertEqual(res["id"], user_settings.id)
        self.assertEqual(res["user"], self.user.id)
        self.assertEqual(res["preferred_currency"], user_settings.preferred_currency_id)
        self.assertEqual(res["active_trip"], user_settings.active_trip_id)

    def test_encrypt_user_data(self):
        password = "password"  # Same as factory default
        category = CategoryFactory(user=self.user)
        trip = TripFactory(user=self.user)
        expense_1 = ExpenseFactory(
            user=self.user,
            category=category,
            trip=trip,
            description="Expense 1",
            amount=10.0,
        )
        expense_2 = ExpenseFactory(
            user=self.user,
            category=category,
            trip=trip,
            description="Expense 2",
            amount=20.5,
        )
        body = {"password": password}
        res = self.client.post(
            reverse("expenses:user-settings-activate-encryption"), body, format="json"
        )
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)
        user_settings = UserSettings.objects.get(user=self.user)
        self.assertTrue(user_settings.is_encrypted)
        expense_1.refresh_from_db()
        expense_2.refresh_from_db()

        # Check that the expenses are encrypted and the original fields are cleared
        self.assertEqual(expense_1.description, "")
        self.assertEqual(expense_1.amount, None)
        self.assertEqual(expense_2.description, "")
        self.assertEqual(expense_2.amount, None)

        self.assertEqual(
            "Expense 1",
            decrypt_text_with_password(
                self.user, password, expense_1.encrypted_description
            ),
        )
        self.assertEqual(
            "10.00",
            decrypt_text_with_password(self.user, password, expense_1.encrypted_amount),
        )
        self.assertEqual(
            "Expense 2",
            decrypt_text_with_password(
                self.user, password, expense_2.encrypted_description
            ),
        )
        self.assertEqual(
            "20.50",
            decrypt_text_with_password(self.user, password, expense_2.encrypted_amount),
        )

    def test_encrypt_user_data_sets_cookie(self):
        password = "password"  # Same as factory default
        body = {"password": password}
        res = self.client.post(
            reverse("expenses:user-settings-activate-encryption"), body, format="json"
        )
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)
        cookie = res.cookies["user_crypto_key"]
        self.assertIsNotNone(cookie)
        self.assertTrue(cookie.value)
