from decimal import Decimal

from django.urls import reverse
from expenses import date_utils
from expenses.models import (
    Expense,
    Notification,
    SharedExpense,
    SharedExpenseParticipant,
)
from expenses.models.notification import NotificationKind
from expenses.tests.api.api_test_case import ApiTestCase
from expenses.tests.factories.category_factories import ExpenseCategoryFactory
from expenses.tests.factories.currency_factories import CurrencyFactory
from expenses.tests.factories.friend_factories import FriendFactory
from expenses.tests.factories.user_factories import UserFactory
from rest_framework import status


class SharedExpenseTestCase(ApiTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.list_url = reverse("expenses:expenses-list")
        cls.euro = CurrencyFactory(code="EUR", symbol="€", display_name="Euro")
        cls.dollar = CurrencyFactory(code="USD", symbol="$", display_name="Dollar")
        cls.me = UserFactory()
        cls.anna = UserFactory()
        cls.bruno = UserFactory()
        cls.stranger = UserFactory()
        FriendFactory(user_1=cls.me, user_2=cls.anna)
        FriendFactory(user_1=cls.bruno, user_2=cls.me)
        cls.my_category = ExpenseCategoryFactory(user=cls.me, code="food", name="Food")
        cls.anna_category = ExpenseCategoryFactory(
            user=cls.anna, code="food", name="Food"
        )

    def expense_body(self, **overrides):
        today = date_utils.today().isoformat()
        body = {
            "expense_date": today,
            "description": "Dinner",
            "amount": "10.00",
            "amortization_start_date": today,
            "amortization_end_date": today,
            "category": self.my_category.id,
            "trip": None,
            "is_expense": True,
            "currency": self.euro.id,
        }
        return {**body, **overrides}

    def share_dinner(self, amount="10.00"):
        """As `me`, share a dinner with Anna and Bruno and return my expense."""
        self.login(self.me.email)
        body = self.expense_body(
            amount=amount, shared_with=[self.anna.id, self.bruno.id]
        )
        res = self.client.post(self.list_url, body, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.logout()
        return Expense.objects.get(id=res.data["id"])

    def participant_of(self, user) -> SharedExpenseParticipant:
        return SharedExpenseParticipant.objects.get(user=user)


class TestShareExpense(SharedExpenseTestCase):
    def test_creator_expense_amount_is_own_quota(self):
        expense = self.share_dinner(amount="30.00")

        self.assertEqual(expense.amount, Decimal("10.00"))

    def test_leftover_cent_goes_to_creator(self):
        self.share_dinner(amount="10.00")

        quotas = {p.user_id: p.quota for p in SharedExpenseParticipant.objects.all()}
        self.assertEqual(
            quotas,
            {
                self.me.id: Decimal("3.34"),
                self.anna.id: Decimal("3.33"),
                self.bruno.id: Decimal("3.33"),
            },
        )

    def test_creator_expense_points_to_own_participant(self):
        expense = self.share_dinner(amount="10.00")

        self.assertEqual(
            expense.shared_expense_participant, self.participant_of(self.me)
        )
        self.assertEqual(expense.shared_expense_participant.quota, Decimal("3.34"))

    def test_shared_expense_stores_the_total(self):
        self.share_dinner(amount="10.00")

        shared_expense = SharedExpense.objects.get()
        self.assertEqual(shared_expense.description, "Dinner")
        self.assertEqual(shared_expense.amount, Decimal("10.00"))
        self.assertEqual(shared_expense.currency, self.euro)
        self.assertEqual(shared_expense.created_by, self.me)

    def test_friends_get_no_expense_until_they_complete_it(self):
        self.share_dinner()

        self.assertFalse(
            Expense.objects.filter(user__in=[self.anna, self.bruno]).exists()
        )

    def test_each_friend_is_notified_of_their_own_share(self):
        self.share_dinner()

        notifications = Notification.objects.order_by("user_id")
        self.assertEqual(
            [
                (
                    n.user_id,
                    n.kind,
                    n.sharedexpensenotification_set.get().shared_expense_participant,
                )
                for n in notifications
            ],
            [
                (
                    self.anna.id,
                    NotificationKind.SHARED_EXPENSE_REQUESTED,
                    self.participant_of(self.anna),
                ),
                (
                    self.bruno.id,
                    NotificationKind.SHARED_EXPENSE_REQUESTED,
                    self.participant_of(self.bruno),
                ),
            ],
        )

    def test_sharing_with_a_non_friend_is_rejected_and_nothing_is_saved(self):
        self.login(self.me.email)
        body = self.expense_body(shared_with=[self.anna.id, self.stranger.id])

        res = self.client.post(self.list_url, body, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Expense.objects.exists())
        self.assertFalse(SharedExpense.objects.exists())
        self.assertFalse(Notification.objects.exists())

    def test_sharing_twice_with_the_same_friend_is_rejected(self):
        self.login(self.me.email)
        body = self.expense_body(shared_with=[self.anna.id, self.anna.id])

        res = self.client.post(self.list_url, body, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sharing_without_currency_is_rejected(self):
        self.login(self.me.email)
        body = self.expense_body(currency=None, shared_with=[self.anna.id])

        res = self.client.post(self.list_url, body, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Expense.objects.exists())

    def test_expense_without_friends_is_not_shared(self):
        self.login(self.me.email)

        res = self.client.post(self.list_url, self.expense_body(), format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Expense.objects.get().amount, Decimal("10.00"))
        self.assertIsNone(Expense.objects.get().shared_expense_participant)
        self.assertFalse(SharedExpense.objects.exists())

    def test_encrypted_creator_expense_holds_own_quota(self):
        self.login(self.me.email)
        self.activate_encryption("password")
        body = self.expense_body(amount="10.00", shared_with=[self.anna.id])

        res = self.client.post(self.list_url, body, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["amount"], "5.00")
        self.assertIsNone(Expense.objects.get().amount)


class TestCompleteSharedExpense(SharedExpenseTestCase):
    def setUp(self):
        self.share_dinner(amount="10.00")
        self.login(self.anna.email)

    def completion_body(self, **overrides):
        body = self.expense_body(
            amount="3.33",
            category=self.anna_category.id,
            shared_expense_participant=self.participant_of(self.anna).id,
        )
        return {**body, **overrides}

    def test_friend_completes_own_share_with_quota(self):
        res = self.client.post(self.list_url, self.completion_body(), format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        expense = Expense.objects.get(user=self.anna)
        self.assertEqual(expense.amount, Decimal("3.33"))
        self.assertEqual(
            expense.shared_expense_participant, self.participant_of(self.anna)
        )

    def test_amount_different_from_quota_is_rejected(self):
        res = self.client.post(
            self.list_url, self.completion_body(amount="5.00"), format="json"
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Expense.objects.filter(user=self.anna).exists())

    def test_currency_different_from_shared_expense_is_rejected(self):
        res = self.client.post(
            self.list_url, self.completion_body(currency=self.dollar.id), format="json"
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_completing_another_users_share_is_rejected(self):
        body = self.completion_body(
            shared_expense_participant=self.participant_of(self.bruno).id
        )

        res = self.client.post(self.list_url, body, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Expense.objects.filter(user=self.anna).exists())

    def test_completing_the_same_share_twice_is_rejected(self):
        self.client.post(self.list_url, self.completion_body(), format="json")

        res = self.client.post(self.list_url, self.completion_body(), format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Expense.objects.filter(user=self.anna).count(), 1)

    def test_completing_expense_cannot_be_shared_again(self):
        body = self.completion_body(shared_with=[self.me.id])

        res = self.client.post(self.list_url, body, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Expense.objects.filter(user=self.anna).exists())


class TestShareExistingExpense(SharedExpenseTestCase):
    def setUp(self):
        self.login(self.me.email)

    def create_expense(self, amount="20.00") -> Expense:
        res = self.client.post(
            self.list_url, self.expense_body(amount=amount), format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        return Expense.objects.get(id=res.data["id"])

    def update(self, expense: Expense, **overrides):
        return self.client.put(
            reverse("expenses:expenses-detail", args=[expense.id]),
            self.expense_body(**overrides),
            format="json",
        )

    def test_unshared_expense_amount_becomes_own_quota(self):
        expense = self.create_expense()

        res = self.update(expense, amount="20.00", shared_with=[self.anna.id])

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expense.refresh_from_db()
        self.assertEqual(expense.amount, Decimal("10.00"))
        self.assertEqual(
            expense.shared_expense_participant, self.participant_of(self.me)
        )

    def test_sharing_on_update_stores_the_shared_expense(self):
        expense = self.create_expense()

        self.update(expense, amount="20.00", shared_with=[self.anna.id, self.bruno.id])

        shared_expense = SharedExpense.objects.get()
        self.assertEqual(shared_expense.amount, Decimal("20.00"))
        self.assertEqual(shared_expense.created_by, self.me)
        quotas = {p.user_id: p.quota for p in SharedExpenseParticipant.objects.all()}
        self.assertEqual(
            quotas,
            {
                self.me.id: Decimal("6.68"),
                self.anna.id: Decimal("6.66"),
                self.bruno.id: Decimal("6.66"),
            },
        )

    def test_sharing_on_update_notifies_friends(self):
        expense = self.create_expense()

        self.update(expense, shared_with=[self.anna.id])

        notification = Notification.objects.get()
        self.assertEqual(notification.user, self.anna)
        self.assertEqual(notification.kind, NotificationKind.SHARED_EXPENSE_REQUESTED)

    def test_update_without_friends_leaves_expense_unshared(self):
        expense = self.create_expense()

        res = self.update(expense, amount="30.00")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expense.refresh_from_db()
        self.assertEqual(expense.amount, Decimal("30.00"))
        self.assertIsNone(expense.shared_expense_participant)
        self.assertFalse(SharedExpense.objects.exists())

    def test_failed_share_on_update_leaves_expense_unchanged(self):
        expense = self.create_expense(amount="20.00")

        res = self.update(expense, amount="50.00", shared_with=[self.stranger.id])

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        expense.refresh_from_db()
        self.assertEqual(expense.amount, Decimal("20.00"))
        self.assertFalse(SharedExpense.objects.exists())

    def test_encrypted_expense_is_shared_on_update(self):
        self.activate_encryption("password")
        expense = self.create_expense(amount="20.00")

        res = self.update(expense, amount="20.00", shared_with=[self.anna.id])

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["amount"], "10.00")
        self.assertEqual(SharedExpense.objects.get().amount, Decimal("20.00"))
