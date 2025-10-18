from rest_framework import status
from rest_framework.test import APITestCase

from expenses.tests.factories.user_factories import UserFactory
from rest_framework.reverse import reverse


class TestLogin(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.url = reverse("expenses:users-login")

    def test_login(self):
        res = self.client.post(
            self.url, {"email": self.user.email, "password": "password"}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res = self.client.get(reverse("expenses:users-self"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res = res.json()
        self.assertEqual(res["email"], self.user.email)

    def test_logout(self):
        res = self.client.post(
            self.url, {"email": self.user.email, "password": "password"}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res = self.client.post(reverse("expenses:users-logout"))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        res = self.client.get(reverse("expenses:users-self"))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
