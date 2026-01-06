from django.urls import reverse
from rest_framework import status

from expenses.models import Settings
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

    def test_create_trip_when_limit_not_set(self):
        """Test that creation works when max_trips is not set"""
        Settings.objects.all().delete()  # Ensure no settings exist
        body = {
            "code": "test_trip",
            "name": "Test Trip",
        }
        res = self.client.post(self.list_url, body, format="json")
        self.assertEqual(res.status_code, 201)

    def test_create_trip_when_limit_not_reached(self):
        """Test that creation works when limit is not reached"""
        Settings.objects.all().delete()
        Settings.objects.create(max_categories=None, max_trips=2)
        
        # Create one trip (limit is 2)
        TripFactory(user=self.user, code="trip1", name="Trip 1")
        
        body = {
            "code": "trip2",
            "name": "Trip 2",
        }
        res = self.client.post(self.list_url, body, format="json")
        self.assertEqual(res.status_code, 201)

    def test_create_trip_when_limit_reached(self):
        """Test that creation fails when limit is reached"""
        Settings.objects.all().delete()
        Settings.objects.create(max_categories=None, max_trips=2)
        
        # Create two trips (reaching the limit of 2)
        TripFactory(user=self.user, code="trip1", name="Trip 1")
        TripFactory(user=self.user, code="trip2", name="Trip 2")
        
        body = {
            "code": "trip3",
            "name": "Trip 3",
        }
        res = self.client.post(self.list_url, body, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("Maximum number of trips (2) has been reached", str(res.data))

    def test_create_trip_limit_per_user(self):
        """Test that limits are per user, not global"""
        Settings.objects.all().delete()
        Settings.objects.create(max_categories=None, max_trips=2)
        
        # Create 2 trips for self.user (reaching limit)
        TripFactory(user=self.user, code="trip1", name="Trip 1")
        TripFactory(user=self.user, code="trip2", name="Trip 2")
        
        # Another user should still be able to create trips
        other_user = UserFactory()
        self.login(other_user.email)
        
        body = {
            "code": "other_trip1",
            "name": "Other Trip 1",
        }
        res = self.client.post(self.list_url, body, format="json")
        self.assertEqual(res.status_code, 201)
