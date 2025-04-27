from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.reverse import reverse


class ApiTestCase(APITestCase):
    def login(self, email, password="password"):
        url = reverse("expenses:users-login")
        res = self.client.post(url, {"email": email, "password": password})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
