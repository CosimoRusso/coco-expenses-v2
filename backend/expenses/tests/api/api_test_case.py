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
