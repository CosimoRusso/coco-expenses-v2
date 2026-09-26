from django.urls import reverse
from expenses.tests.api.api_test_case import ApiTestCase
from expenses.tests.factories.friend_factories import FriendFactory
from expenses.tests.factories.user_factories import UserFactory
from rest_framework import status


class TestFriends(ApiTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(first_name="Me")
        cls.list_url = reverse("expenses:friends-list")

    def setUp(self):
        self.login(self.user.email)

    def test_list_includes_friend_where_user_is_user_1(self):
        friend = UserFactory()
        FriendFactory(user_1=self.user, user_2=friend)

        res = self.client.get(self.list_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual([f["id"] for f in res.data], [friend.id])

    def test_list_includes_friend_where_user_is_user_2(self):
        friend = UserFactory()
        FriendFactory(user_1=friend, user_2=self.user)

        res = self.client.get(self.list_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual([f["id"] for f in res.data], [friend.id])

    def test_list_excludes_friendships_of_other_users(self):
        FriendFactory()
        UserFactory()

        res = self.client.get(self.list_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, [])

    def test_list_returns_friend_once_when_linked_in_both_directions(self):
        friend = UserFactory()
        FriendFactory(user_1=self.user, user_2=friend)
        FriendFactory(user_1=friend, user_2=self.user)

        res = self.client.get(self.list_url)

        self.assertEqual([f["id"] for f in res.data], [friend.id])

    def test_list_is_ordered_by_name(self):
        zoe = UserFactory(first_name="Zoe", last_name="Bianchi")
        anna_verdi = UserFactory(first_name="Anna", last_name="Verdi")
        anna_rossi = UserFactory(first_name="Anna", last_name="Rossi")
        FriendFactory(user_1=self.user, user_2=zoe)
        FriendFactory(user_1=anna_verdi, user_2=self.user)
        FriendFactory(user_1=self.user, user_2=anna_rossi)

        res = self.client.get(self.list_url)

        self.assertEqual(
            [f["id"] for f in res.data], [anna_rossi.id, anna_verdi.id, zoe.id]
        )

    def test_list_exposes_only_public_fields(self):
        friend = UserFactory(
            first_name="Anna", last_name="Rossi", email="anna@test.com"
        )
        FriendFactory(user_1=self.user, user_2=friend)

        res = self.client.get(self.list_url)

        self.assertEqual(
            res.data,
            [
                {
                    "id": friend.id,
                    "first_name": "Anna",
                    "last_name": "Rossi",
                    "email": "anna@test.com",
                }
            ],
        )

    def test_list_requires_authentication(self):
        self.logout()

        res = self.client.get(self.list_url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
