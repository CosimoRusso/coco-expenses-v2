from decimal import Decimal

from django.urls import reverse
from expenses import date_utils
from expenses.models import Expense
from expenses.sharing import ExpenseShare, create_shared_expense
from expenses.tests.api.api_test_case import ApiTestCase
from expenses.tests.factories.category_factories import ExpenseCategoryFactory
from expenses.tests.factories.currency_factories import CurrencyFactory
from expenses.tests.factories.user_factories import UserFactory
from rest_framework import status


class TestNotifications(ApiTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.list_url = reverse("expenses:notifications-list")
        cls.unread_count_url = reverse("expenses:notifications-unread-count")
        cls.euro = CurrencyFactory(code="EUR", symbol="€", display_name="Euro")
        cls.creator = UserFactory(first_name="Carla", last_name="Neri")
        cls.me = UserFactory()

    def setUp(self):
        self.login(self.me.email)

    def share_with_me(self, description="Dinner", total="10.00"):
        """Have the creator share an expense with me and return my participant."""
        share = ExpenseShare(
            creator=self.creator,
            friends=[self.me],
            description=description,
            total=Decimal(total),
            currency=self.euro,
        )
        create_shared_expense(share)
        return self.me.sharedexpenseparticipant_set.get(
            shared_expense__description=description
        )

    def read_url(self, notification_id: int) -> str:
        return reverse("expenses:notifications-read", args=[notification_id])

    def test_list_contains_only_my_notifications_newest_first(self):
        self.share_with_me(description="Lunch")
        self.share_with_me(description="Dinner")
        create_shared_expense(
            ExpenseShare(
                creator=self.me,
                friends=[self.creator],
                description="Taxi",
                total=Decimal("8.00"),
                currency=self.euro,
            )
        )

        res = self.client.get(self.list_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [n["shared_expense"]["description"] for n in res.data], ["Dinner", "Lunch"]
        )

    def test_list_describes_the_share_to_complete(self):
        participant = self.share_with_me(total="10.00")

        res = self.client.get(self.list_url)

        notification = res.data[0]
        self.assertEqual(notification["kind"], "SHARED_EXPENSE_REQUESTED")
        self.assertIsNone(notification["read_at"])
        self.assertEqual(
            notification["shared_expense"],
            {
                "id": participant.id,
                "quota": "5.00",
                "description": "Dinner",
                "total_amount": "10.00",
                "currency": self.euro.id,
                "created_by": "Carla Neri",
                "is_completed": False,
            },
        )

    def test_share_is_completed_once_i_add_my_expense(self):
        participant = self.share_with_me(total="10.00")
        today = date_utils.today().isoformat()
        body = {
            "expense_date": today,
            "description": "Dinner",
            "amount": "5.00",
            "amortization_start_date": today,
            "amortization_end_date": today,
            "category": ExpenseCategoryFactory(user=self.me).id,
            "is_expense": True,
            "currency": self.euro.id,
            "shared_expense_participant": participant.id,
        }
        self.client.post(reverse("expenses:expenses-list"), body, format="json")

        res = self.client.get(self.list_url)

        self.assertTrue(Expense.objects.filter(user=self.me).exists())
        self.assertTrue(res.data[0]["shared_expense"]["is_completed"])

    def test_read_marks_the_notification_as_read(self):
        self.share_with_me()
        notification = self.me.notification_set.get()

        res = self.client.post(self.read_url(notification.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        notification.refresh_from_db()
        self.assertIsNotNone(notification.read_at)
        self.assertIsNotNone(res.data["read_at"])

    def test_reading_again_keeps_the_first_read_time(self):
        self.share_with_me()
        notification = self.me.notification_set.get()
        self.client.post(self.read_url(notification.id))
        notification.refresh_from_db()
        first_read_at = notification.read_at

        self.client.post(self.read_url(notification.id))

        notification.refresh_from_db()
        self.assertEqual(notification.read_at, first_read_at)

    def test_unread_count_excludes_read_notifications(self):
        self.share_with_me(description="Lunch")
        self.share_with_me(description="Dinner")
        self.client.post(self.read_url(self.me.notification_set.first().id))

        res = self.client.get(self.unread_count_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {"count": 1})

    def test_cannot_read_another_users_notification(self):
        create_shared_expense(
            ExpenseShare(
                creator=self.me,
                friends=[self.creator],
                description="Taxi",
                total=Decimal("8.00"),
                currency=self.euro,
            )
        )
        others_notification = self.creator.notification_set.get()

        res = self.client.post(self.read_url(others_notification.id))

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        others_notification.refresh_from_db()
        self.assertIsNone(others_notification.read_at)
