from django.urls import reverse

from expenses.tests.api.api_test_case import ApiTestCase
from expenses.tests.factories.trip_factories import TripFactory
from expenses.tests.factories.user_factories import UserFactory


class TestTrips(ApiTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.list_url = reverse("expenses:trips-list")

    def details_url(self, id: int) -> str:
        return reverse("expenses:trips-detail", args=[id])

    def setUp(self):
        self.login(self.user.email)

    def test_create_trip(self):
        body = {
            "code": "test_trip",
            "name": "Test Trip",
        }
        url = reverse("expenses:trips-list")
        res = self.client.post(url, body, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["code"], body["code"])
        self.assertEqual(res.data["name"], body["name"])
        self.assertTrue(res.data["is_active"])  # Default should be True

    def test_update_trip(self):
        trip = TripFactory(user=self.user)

        update_body = {
            "code": "updated_trip",
            "name": "Updated Trip",
            "is_active": False,
        }
        res = self.client.put(self.details_url(trip.id), update_body, format="json")
        self.assertEqual(res.status_code, 200)
        trip.refresh_from_db()
        self.assertEqual(trip.code, update_body["code"])
        self.assertEqual(trip.name, update_body["name"])
        self.assertFalse(trip.is_active)

    def test_list_trips(self):
        other_user = UserFactory()
        other_trip = TripFactory(user=other_user)
        trips = [
            TripFactory(user=self.user),
            TripFactory(user=self.user),
        ]

        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 2)
        for trip in trips:
            self.assertIn(trip.code, [t["code"] for t in res.data])
            self.assertIn(trip.id, [t["id"] for t in res.data])

        self.assertNotIn(other_trip.code, [t["code"] for t in res.data])

    def test_filter_trips_by_is_active(self):
        active_trip = TripFactory(user=self.user, is_active=True)
        inactive_trip = TripFactory(user=self.user, is_active=False)

        # Filter by active
        res = self.client.get(self.list_url, {"is_active": "true"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["id"], active_trip.id)

        # Filter by inactive
        res = self.client.get(self.list_url, {"is_active": "false"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["id"], inactive_trip.id)
