from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase


class ApiTestCase(APITestCase):
    def login(self, email, password="password"):
        url = reverse("expenses:users-login")
        res = self.client.post(url, {"email": email, "password": password})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def logout(self):
        url = reverse("expenses:users-logout")
        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def activate_encryption(self, password: str) -> None:
        response = self.client.post(
            reverse("expenses:user-settings-activate-encryption"),
            {"password": password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
