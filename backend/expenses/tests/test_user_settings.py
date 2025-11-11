from django.urls import reverse
from rest_framework import status as http_status
from expenses.tests.api.api_test_case import ApiTestCase
from expenses.tests.factories.user_factories import UserFactory
from expenses.tests.factories.currency_factories import CurrencyFactory
from expenses.tests.factories.trip_factories import TripFactory
from expenses.tests.factories.user_settings_factories import UserSettingsFactory
from expenses.models.currency import Currency

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

    def test_create_user_settings(self):
        body = {
            "preferred_currency": 1,
            "active_trip": 1
        }
        res = self.client.post(self.list_url, body, format="json")
        self.assertEqual(res.status_code, http_status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_settings(self):
        user_settings = UserSettingsFactory(user=self.user)
        body = {
            "preferred_currency": self.currency.id,
            "active_trip": self.trip.id
        }
        res = self.client.patch(self.details_url(user_settings.id), body, format="json")
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)
        user_settings.refresh_from_db()
        self.assertEqual(user_settings.preferred_currency, self.currency)
        self.assertEqual(user_settings.active_trip, self.trip)

    def test_get_user_settings(self):
        user_settings = UserSettingsFactory(user=self.user)
        res = self.client.get(self.details_url(user_settings.id))
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)
        self.assertEqual(res.data["preferred_currency"], user_settings.preferred_currency_id)
        self.assertEqual(res.data["active_trip"], user_settings.active_trip_id)

    def cannot_get_user_settings_for_other_user(self):
        other_user = UserFactory()
        other_user_settings = UserSettingsFactory(user=other_user)
        res = self.client.get(self.details_url(other_user_settings.id))
        self.assertEqual(res.status_code, http_status.HTTP_404_NOT_FOUND)

    def test_self_user_settings(self):
        user_settings = UserSettingsFactory(user=self.user)
        res = self.client.get(reverse("expenses:user-settings-self"))
        self.assertEqual(res.status_code, http_status.HTTP_200_OK)
        res = res.json()
        self.assertEqual(res["id"], user_settings.id)
        self.assertEqual(res["user"], self.user.id)
        self.assertEqual(res["preferred_currency"], user_settings.preferred_currency_id)
        self.assertEqual(res["active_trip"], user_settings.active_trip_id)