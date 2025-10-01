from expenses.models.user import User
from rest_framework import status
from rest_framework.test import APITestCase

from expenses.tests.factories.user_factories import UserFactory
from rest_framework.reverse import reverse


class TestRegister(APITestCase):
    def setUp(self):
        self.url = reverse("expenses:users-register")

    def test_register(self):
        res = self.client.post(
            self.url, {"email": "test@test.com", "password": "password", "password_confirmation": "password", "first_name": "John", "last_name": "Doe"}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res = res.json()
        user = User.objects.get(email="test@test.com")
        self.assertEqual(user.email, "test@test.com")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")

    def test_register_with_existing_email(self):
        UserFactory(email="test@test.com")
        res = self.client.post(
            self.url, {"email": "test@test.com", "password": "password", "password_confirmation": "password", "first_name": "John", "last_name": "Doe"}
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.json()["email"], ["Email already exists"])

    def test_register_with_short_password(self):
        res = self.client.post(
            self.url, {"email": "test@test.com", "password": "pass", "password_confirmation": "pass", "first_name": "John", "last_name": "Doe"}
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.json()["password"], ["Password must be at least 6 characters long"])

    def test_register_with_missing_fields(self):
        res = self.client.post(
            self.url, {}
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.json()["email"], ["This field is required."])
        self.assertEqual(res.json()["password"], ["This field is required."])
        self.assertEqual(res.json()["first_name"], ["This field is required."])
        self.assertEqual(res.json()["last_name"], ["This field is required."])

    def test_register_with_invalid_email(self):
        res = self.client.post(
            self.url, {"email": "test@test", "password": "password", "password_confirmation": "password", "first_name": "John", "last_name": "Doe"}
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.json()["email"], ["Enter a valid email address."])

    def test_register_with_password_confirmation_mismatch(self):
        res = self.client.post(
            self.url, {"email": "test@test.com", "password": "password", "password_confirmation": "password1", "first_name": "John", "last_name": "Doe"}
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.json()["password"], ["Password confirmation does not match"])