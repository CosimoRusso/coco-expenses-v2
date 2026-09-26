from decimal import Decimal

from django.urls import reverse
from expenses.models import (
    Expense,
    Notification,
    SharedExpense,
    SharedExpenseModifiedNotification,
    SharedExpenseParticipant,
)
from expenses.models.notification import NotificationKind
from expenses.tests.api.test_shared_expenses import SharedExpenseTestCase
from expenses.tests.factories.friend_factories import FriendFactory
from expenses.tests.factories.trip_factories import TripFactory
from expenses.tests.factories.user_factories import UserFactory
from rest_framework import status


class EditSharedExpenseTestCase(SharedExpenseTestCase):
    """I shared 30.00 with Anna and Bruno; Anna completed her share, Bruno did not."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.dave = UserFactory()
        cls.carla = UserFactory()
        FriendFactory(user_1=cls.me, user_2=cls.dave)
        FriendFactory(user_1=cls.anna, user_2=cls.carla)

    def setUp(self):
        self.my_expense = self.share_dinner(amount="30.00")
        self.login(self.anna.email)
        res = self.client.post(
            self.list_url,
            self.expense_body(
                amount="10.00",
                category=self.anna_category.id,
                shared_expense_participant=self.participant_of(self.anna).id,
            ),
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.anna_expense = Expense.objects.get(id=res.data["id"])
        self.logout()

    def edit(self, user, expense: Expense, **overrides):
        """Log in as `user` and update `expense` with the shared total by default."""
        self.login(user.email)
        category = self.my_category if user == self.me else self.anna_category
        defaults = {"amount": "30.00", "category": category.id}
        body = self.expense_body(**{**defaults, **overrides})
        return self.client.put(
            reverse("expenses:expenses-detail", args=[expense.id]), body, format="json"
        )

    def modifications(self) -> dict[int, SharedExpenseModifiedNotification]:
        """The modification notifications sent, by recipient user id."""
        return {
            m.notification.user_id: m
            for m in SharedExpenseModifiedNotification.objects.select_related(
                "notification"
            )
        }

    def quotas(self) -> dict[int, Decimal]:
        return {p.user_id: p.quota for p in SharedExpenseParticipant.objects.all()}


class TestEditPersonalFields(EditSharedExpenseTestCase):
    def test_personal_fields_change_without_notifying_anyone(self):
        trip = TripFactory(user=self.me)

        res = self.edit(
            self.me,
            self.my_expense,
            description="My dinner",
            trip=trip.id,
            shared_with=[self.anna.id, self.bruno.id],
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.my_expense.refresh_from_db()
        self.assertEqual(self.my_expense.description, "My dinner")
        self.assertEqual(self.my_expense.trip, trip)
        self.assertFalse(SharedExpenseModifiedNotification.objects.exists())
        self.assertEqual(SharedExpense.objects.get().amount, Decimal("30.00"))

    def test_saving_the_current_total_updates_a_stale_expense_to_the_quota(self):
        self.edit(self.me, self.my_expense, amount="60.00")
        modifications_before = SharedExpenseModifiedNotification.objects.count()

        res = self.edit(self.anna, self.anna_expense, amount="60.00")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.anna_expense.refresh_from_db()
        self.assertEqual(self.anna_expense.amount, Decimal("20.00"))
        self.assertEqual(
            SharedExpenseModifiedNotification.objects.count(), modifications_before
        )


class TestEditTotalAndCurrency(EditSharedExpenseTestCase):
    def test_new_total_is_split_again_between_participants(self):
        res = self.edit(self.me, self.my_expense, amount="40.00")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(SharedExpense.objects.get().amount, Decimal("40.00"))
        self.assertEqual(
            self.quotas(),
            {
                self.me.id: Decimal("13.34"),
                self.anna.id: Decimal("13.33"),
                self.bruno.id: Decimal("13.33"),
            },
        )

    def test_editor_expense_gets_the_new_quota(self):
        self.edit(self.me, self.my_expense, amount="40.00")

        self.my_expense.refresh_from_db()
        self.assertEqual(self.my_expense.amount, Decimal("13.34"))

    def test_other_participants_expenses_keep_their_amount(self):
        self.edit(self.me, self.my_expense, amount="40.00")

        self.anna_expense.refresh_from_db()
        self.assertEqual(self.anna_expense.amount, Decimal("10.00"))

    def test_other_participants_are_notified_of_the_new_total(self):
        self.edit(self.me, self.my_expense, amount="40.00")

        modifications = self.modifications()
        self.assertEqual(set(modifications), {self.anna.id, self.bruno.id})
        anna_modification = modifications[self.anna.id]
        self.assertEqual(
            anna_modification.notification.kind,
            NotificationKind.SHARED_EXPENSE_MODIFIED,
        )
        self.assertEqual(anna_modification.modified_by, self.me)
        self.assertEqual(anna_modification.amount_before, Decimal("30.00"))
        self.assertEqual(anna_modification.amount_after, Decimal("40.00"))
        self.assertEqual(anna_modification.number_participants_before, 3)
        self.assertEqual(anna_modification.number_participants_after, 3)
        self.assertFalse(anna_modification.you_were_added)
        self.assertFalse(anna_modification.you_were_removed)

    def test_new_currency_applies_to_everyone(self):
        self.edit(self.me, self.my_expense, currency=self.dollar.id)

        self.my_expense.refresh_from_db()
        self.assertEqual(SharedExpense.objects.get().currency, self.dollar)
        self.assertEqual(self.my_expense.currency, self.dollar)
        anna_modification = self.modifications()[self.anna.id]
        self.assertEqual(anna_modification.currency_before, self.euro)
        self.assertEqual(anna_modification.currency_after, self.dollar)

    def test_non_creator_can_change_the_total(self):
        res = self.edit(
            self.anna,
            self.anna_expense,
            amount="60.00",
            shared_with=[self.me.id, self.bruno.id],
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.anna_expense.refresh_from_db()
        self.assertEqual(self.anna_expense.amount, Decimal("20.00"))
        self.assertEqual(set(self.modifications()), {self.me.id, self.bruno.id})

    def test_missing_amount_is_rejected(self):
        res = self.edit(self.me, self.my_expense, amount=None)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SharedExpense.objects.get().amount, Decimal("30.00"))


class TestEditSplit(EditSharedExpenseTestCase):
    def split(self, *quotas: tuple) -> list[dict]:
        return [{"user": user.id, "quota": quota} for user, quota in quotas]

    def test_editor_sets_the_quota_of_everyone(self):
        split = self.split(
            (self.me, "20.00"), (self.anna, "6.00"), (self.bruno, "4.00")
        )

        res = self.edit(self.anna, self.anna_expense, split=split)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.quotas(),
            {
                self.me.id: Decimal("20.00"),
                self.anna.id: Decimal("6.00"),
                self.bruno.id: Decimal("4.00"),
            },
        )

    def test_editor_expense_gets_own_quota_of_the_split(self):
        split = self.split(
            (self.me, "20.00"), (self.anna, "6.00"), (self.bruno, "4.00")
        )

        self.edit(self.anna, self.anna_expense, split=split)

        self.anna_expense.refresh_from_db()
        self.assertEqual(self.anna_expense.amount, Decimal("6.00"))

    def test_changing_only_the_split_notifies_the_others(self):
        split = self.split(
            (self.me, "20.00"), (self.anna, "6.00"), (self.bruno, "4.00")
        )

        self.edit(self.anna, self.anna_expense, split=split)

        self.assertEqual(set(self.modifications()), {self.me.id, self.bruno.id})

    def test_negative_quota_is_rejected_and_quotas_are_unchanged(self):
        split = self.split(
            (self.me, "-5.00"), (self.anna, "25.00"), (self.bruno, "10.00")
        )

        res = self.edit(self.anna, self.anna_expense, split=split)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.quotas()[self.me.id], Decimal("10.00"))

    def test_added_friend_needs_a_quota_in_the_split(self):
        split = self.split(
            (self.me, "20.00"), (self.anna, "6.00"), (self.bruno, "4.00")
        )

        res = self.edit(
            self.me,
            self.my_expense,
            shared_with=[self.anna.id, self.bruno.id, self.dave.id],
            split=split,
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn(self.dave.id, self.quotas())

    def test_edit_without_split_splits_the_total_equally_again(self):
        split = self.split(
            (self.me, "20.00"), (self.anna, "6.00"), (self.bruno, "4.00")
        )
        self.edit(self.anna, self.anna_expense, split=split)

        self.edit(self.me, self.my_expense, amount="30.00")

        self.assertEqual(
            self.quotas(),
            {
                self.me.id: Decimal("10.00"),
                self.anna.id: Decimal("10.00"),
                self.bruno.id: Decimal("10.00"),
            },
        )


class TestEditParticipants(EditSharedExpenseTestCase):
    def test_added_friend_becomes_a_participant(self):
        res = self.edit(
            self.me,
            self.my_expense,
            amount="40.00",
            shared_with=[self.anna.id, self.bruno.id, self.dave.id],
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.quotas(),
            {
                self.me.id: Decimal("10.00"),
                self.anna.id: Decimal("10.00"),
                self.bruno.id: Decimal("10.00"),
                self.dave.id: Decimal("10.00"),
            },
        )

    def test_added_friend_is_told_they_were_added(self):
        self.edit(
            self.me,
            self.my_expense,
            shared_with=[self.anna.id, self.bruno.id, self.dave.id],
        )

        modifications = self.modifications()
        self.assertTrue(modifications[self.dave.id].you_were_added)
        self.assertFalse(modifications[self.anna.id].you_were_added)
        self.assertEqual(modifications[self.dave.id].number_participants_before, 3)
        self.assertEqual(modifications[self.dave.id].number_participants_after, 4)

    def test_removed_participant_loses_share_and_expense(self):
        res = self.edit(self.me, self.my_expense, shared_with=[self.bruno.id])

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(Expense.objects.filter(id=self.anna_expense.id).exists())
        self.assertEqual(
            self.quotas(),
            {self.me.id: Decimal("15.00"), self.bruno.id: Decimal("15.00")},
        )
        self.assertTrue(self.modifications()[self.anna.id].you_were_removed)

    def test_removed_participant_loses_pending_share_request(self):
        request_before = Notification.objects.filter(
            user=self.bruno, kind=NotificationKind.SHARED_EXPENSE_REQUESTED
        ).count()

        self.edit(self.me, self.my_expense, shared_with=[self.anna.id])

        request_after = Notification.objects.filter(
            user=self.bruno, kind=NotificationKind.SHARED_EXPENSE_REQUESTED
        ).count()
        self.assertEqual((request_before, request_after), (1, 0))

    def test_non_creator_can_add_own_friend(self):
        res = self.edit(
            self.anna,
            self.anna_expense,
            shared_with=[self.me.id, self.bruno.id, self.carla.id],
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(self.carla.id, self.quotas())

    def test_non_creator_cannot_add_someone_who_is_not_their_friend(self):
        res = self.edit(
            self.anna,
            self.anna_expense,
            shared_with=[self.me.id, self.bruno.id, self.dave.id],
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn(self.dave.id, self.quotas())

    def test_creator_cannot_be_removed(self):
        res = self.edit(self.anna, self.anna_expense, shared_with=[self.bruno.id])

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(self.me.id, self.quotas())
        self.assertFalse(SharedExpenseModifiedNotification.objects.exists())

    def test_removing_everyone_else_is_rejected(self):
        res = self.edit(self.me, self.my_expense, shared_with=[])

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(self.quotas()), 3)

    def test_sharing_with_yourself_is_rejected(self):
        res = self.edit(
            self.me,
            self.my_expense,
            shared_with=[self.me.id, self.anna.id, self.bruno.id],
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_participants_are_kept_when_not_sent(self):
        res = self.edit(self.me, self.my_expense, amount="60.00")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.quotas(),
            {
                self.me.id: Decimal("20.00"),
                self.anna.id: Decimal("20.00"),
                self.bruno.id: Decimal("20.00"),
            },
        )

    def test_encrypted_editor_gets_the_new_quota(self):
        self.login(self.me.email)
        self.activate_encryption("password")

        res = self.edit(self.me, self.my_expense, amount="60.00")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["amount"], "20.00")


class TestSharedExpenseRepresentation(EditSharedExpenseTestCase):
    def test_expense_describes_the_shared_expense(self):
        self.login(self.anna.email)

        res = self.client.get(
            reverse("expenses:expenses-detail", args=[self.anna_expense.id])
        )

        self.assertEqual(
            res.data["shared_expense"],
            {
                "id": SharedExpense.objects.get().id,
                "total_amount": "30.00",
                "currency": self.euro.id,
                "created_by": self.me.id,
                "participants": [
                    {
                        "id": self.participant_of(user).id,
                        "user_id": user.id,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "quota": "10.00",
                    }
                    for user in (self.anna, self.bruno, self.me)
                ],
            },
        )


class TestModifiedNotificationApi(EditSharedExpenseTestCase):
    def modified_notification_of(self, user) -> dict:
        self.login(user.email)
        res = self.client.get(reverse("expenses:notifications-list"))
        return next(n for n in res.data if n["kind"] == "SHARED_EXPENSE_MODIFIED")

    def test_notification_lists_every_change(self):
        self.edit(self.me, self.my_expense, amount="40.00", currency=self.dollar.id)

        notification = self.modified_notification_of(self.anna)

        self.assertEqual(
            notification["modification"],
            {
                "description": "Dinner",
                "modified_by": f"{self.me.first_name} {self.me.last_name}",
                "amount_before": "30.00",
                "currency_before": self.euro.id,
                "amount_after": "40.00",
                "currency_after": self.dollar.id,
                "number_participants_before": 3,
                "number_participants_after": 3,
                "you_were_added": False,
                "you_were_removed": False,
            },
        )

    def test_notification_points_to_the_expense_to_update(self):
        self.edit(self.me, self.my_expense, amount="40.00")

        notification = self.modified_notification_of(self.anna)

        self.assertEqual(
            notification["shared_expense"]["expense_id"], self.anna_expense.id
        )
        self.assertEqual(notification["shared_expense"]["quota"], "13.33")

    def test_added_user_can_complete_from_the_notification(self):
        self.edit(
            self.me,
            self.my_expense,
            shared_with=[self.anna.id, self.bruno.id, self.dave.id],
        )

        notification = self.modified_notification_of(self.dave)

        self.assertTrue(notification["modification"]["you_were_added"])
        self.assertFalse(notification["shared_expense"]["is_completed"])
        self.assertEqual(
            notification["shared_expense"]["id"], self.participant_of(self.dave).id
        )

    def test_removed_user_has_no_share_left(self):
        self.edit(self.me, self.my_expense, shared_with=[self.bruno.id])

        notification = self.modified_notification_of(self.anna)

        self.assertTrue(notification["modification"]["you_were_removed"])
        self.assertIsNone(notification["shared_expense"])


class TestUpdateResponse(EditSharedExpenseTestCase):
    def test_update_response_lists_the_participants_after_the_change(self):
        res = self.edit(
            self.me, self.my_expense, shared_with=[self.bruno.id, self.dave.id]
        )

        self.assertEqual(
            sorted(p["user_id"] for p in res.data["shared_expense"]["participants"]),
            sorted([self.me.id, self.bruno.id, self.dave.id]),
        )

    def test_update_response_shows_the_new_total(self):
        res = self.edit(self.me, self.my_expense, amount="60.00")

        self.assertEqual(res.data["shared_expense"]["total_amount"], "60.00")
        self.assertEqual(res.data["amount"], "20.00")
