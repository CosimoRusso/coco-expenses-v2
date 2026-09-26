from decimal import Decimal

from django.urls import reverse
from expenses.models import (
    Expense,
    Notification,
    SharedExpense,
    SharedExpenseDeletedNotification,
    SharedExpenseParticipant,
)
from expenses.models.notification import NotificationKind
from expenses.tests.api.test_edit_shared_expenses import EditSharedExpenseTestCase
from rest_framework import status


class TestDeleteSharedExpense(EditSharedExpenseTestCase):
    """I shared 30.00 with Anna and Bruno; Anna completed her share, Bruno did not."""

    def delete(self, user, expense: Expense):
        self.login(user.email)
        return self.client.delete(
            reverse("expenses:expenses-detail", args=[expense.id])
        )

    def deletions(self) -> dict[int, SharedExpenseDeletedNotification]:
        """The deletion notifications sent, by recipient user id."""
        return {
            d.notification.user_id: d
            for d in SharedExpenseDeletedNotification.objects.select_related(
                "notification"
            )
        }

    def test_expense_is_deleted_for_every_participant(self):
        res = self.delete(self.me, self.my_expense)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Expense.objects.exists())

    def test_shared_expense_and_participants_are_deleted(self):
        self.delete(self.me, self.my_expense)

        self.assertFalse(SharedExpense.objects.exists())
        self.assertFalse(SharedExpenseParticipant.objects.exists())

    def test_other_participants_are_notified_with_what_was_deleted(self):
        self.delete(self.me, self.my_expense)

        deletions = self.deletions()
        self.assertEqual(set(deletions), {self.anna.id, self.bruno.id})
        anna_deletion = deletions[self.anna.id]
        self.assertEqual(
            anna_deletion.notification.kind, NotificationKind.SHARED_EXPENSE_DELETED
        )
        self.assertEqual(anna_deletion.deleted_by, self.me)
        self.assertEqual(anna_deletion.description, "Dinner")
        self.assertEqual(anna_deletion.amount, Decimal("30.00"))
        self.assertEqual(anna_deletion.currency, self.euro)

    def test_any_participant_can_delete_it(self):
        res = self.delete(self.anna, self.anna_expense)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Expense.objects.exists())
        self.assertEqual(set(self.deletions()), {self.me.id, self.bruno.id})

    def test_notifications_about_the_deleted_expense_are_removed(self):
        self.edit(self.me, self.my_expense, amount="60.00")

        self.delete(self.anna, self.anna_expense)

        self.assertEqual(
            set(Notification.objects.values_list("kind", flat=True)),
            {NotificationKind.SHARED_EXPENSE_DELETED},
        )

    def test_balances_no_longer_count_the_deleted_expense(self):
        self.delete(self.anna, self.anna_expense)

        self.login(self.me.email)
        res = self.client.get(reverse("expenses:balances-list"))
        self.assertEqual(res.data["balances"], [])

    def test_unshared_expense_is_deleted_without_notifications(self):
        self.login(self.me.email)
        res = self.client.post(self.list_url, self.expense_body(), format="json")
        expense = Expense.objects.get(id=res.data["id"])

        res = self.delete(self.me, expense)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Expense.objects.filter(id=expense.id).exists())
        self.assertFalse(SharedExpenseDeletedNotification.objects.exists())
        self.assertTrue(SharedExpense.objects.exists())

    def test_cannot_delete_another_users_expense(self):
        res = self.delete(self.bruno, self.my_expense)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Expense.objects.count(), 2)

    def test_notification_describes_the_deletion(self):
        self.delete(self.me, self.my_expense)

        self.login(self.anna.email)
        res = self.client.get(reverse("expenses:notifications-list"))

        notification = res.data[0]
        self.assertEqual(notification["kind"], "SHARED_EXPENSE_DELETED")
        self.assertIsNone(notification["shared_expense"])
        self.assertEqual(
            notification["deletion"],
            {
                "deleted_by": f"{self.me.first_name} {self.me.last_name}",
                "description": "Dinner",
                "amount": "30.00",
                "currency": self.euro.id,
            },
        )
