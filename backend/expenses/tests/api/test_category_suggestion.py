from decimal import Decimal

from django.urls import reverse
from expenses.models import Notification, SharedExpenseParticipant
from expenses.sharing import ExpenseShare, create_shared_expense
from expenses.tests.api.api_test_case import ApiTestCase
from expenses.tests.factories.category_factories import ExpenseCategoryFactory
from expenses.tests.factories.currency_factories import CurrencyFactory
from expenses.tests.factories.expense_factories import ExpenseFactory
from expenses.tests.factories.user_factories import UserFactory


class TestSuggestedCategory(ApiTestCase):
    """Anna shares expenses with me; I complete them under my own categories."""

    @classmethod
    def setUpTestData(cls):
        cls.euro = CurrencyFactory(code="EUR", symbol="€", display_name="Euro")
        cls.anna = UserFactory()
        cls.me = UserFactory()
        cls.anna_restaurants = ExpenseCategoryFactory(user=cls.anna, code="restaurants")
        cls.anna_travel = ExpenseCategoryFactory(user=cls.anna, code="travel")
        cls.my_food = ExpenseCategoryFactory(user=cls.me, code="food")
        cls.my_fun = ExpenseCategoryFactory(user=cls.me, code="fun")
        cls.my_gifts = ExpenseCategoryFactory(user=cls.me, code="gifts")

    def setUp(self):
        self.login(self.me.email)

    def anna_shares(self, category) -> SharedExpenseParticipant:
        """Have Anna share an expense of `category` with me and return my participant."""
        share = ExpenseShare(
            creator=self.anna,
            friends=[self.me],
            description="Shared",
            total=Decimal("10.00"),
            currency=self.euro,
        )
        anna_participant = create_shared_expense(share)
        ExpenseFactory(
            user=self.anna,
            category=category,
            shared_expense_participant=anna_participant,
        )
        return SharedExpenseParticipant.objects.get(
            shared_expense=anna_participant.shared_expense, user=self.me
        )

    def complete(self, anna_category, my_category) -> None:
        """Have Anna share an expense of `anna_category`, which I save as `my_category`."""
        ExpenseFactory(
            user=self.me,
            category=my_category,
            shared_expense_participant=self.anna_shares(anna_category),
        )

    def suggestion_for(self, anna_category) -> int | None:
        """The category suggested for a new expense Anna shares under `anna_category`."""
        self.anna_shares(anna_category)
        notification = Notification.objects.filter(user=self.me).latest("id")
        url = reverse("expenses:notifications-detail", args=[notification.id])
        return self.client.get(url).data["shared_expense"]["suggested_category"]

    def test_category_used_for_two_of_the_last_three_is_suggested(self):
        self.complete(self.anna_restaurants, self.my_food)
        self.complete(self.anna_restaurants, self.my_fun)
        self.complete(self.anna_restaurants, self.my_food)

        suggestion = self.suggestion_for(self.anna_restaurants)

        self.assertEqual(suggestion, self.my_food.id)

    def test_nothing_is_suggested_with_fewer_than_three_expenses(self):
        self.complete(self.anna_restaurants, self.my_food)
        self.complete(self.anna_restaurants, self.my_food)

        suggestion = self.suggestion_for(self.anna_restaurants)

        self.assertIsNone(suggestion)

    def test_nothing_is_suggested_when_the_last_three_all_differ(self):
        self.complete(self.anna_restaurants, self.my_food)
        self.complete(self.anna_restaurants, self.my_fun)
        self.complete(self.anna_restaurants, self.my_gifts)

        suggestion = self.suggestion_for(self.anna_restaurants)

        self.assertIsNone(suggestion)

    def test_only_the_last_three_expenses_count(self):
        self.complete(self.anna_restaurants, self.my_food)
        self.complete(self.anna_restaurants, self.my_food)
        self.complete(self.anna_restaurants, self.my_food)
        self.complete(self.anna_restaurants, self.my_fun)
        self.complete(self.anna_restaurants, self.my_fun)

        suggestion = self.suggestion_for(self.anna_restaurants)

        self.assertEqual(suggestion, self.my_fun.id)

    def test_expenses_the_friend_saved_under_another_category_do_not_count(self):
        self.complete(self.anna_travel, self.my_food)
        self.complete(self.anna_travel, self.my_food)
        self.complete(self.anna_travel, self.my_food)

        suggestion = self.suggestion_for(self.anna_restaurants)

        self.assertIsNone(suggestion)

    def test_expenses_shared_by_another_friend_do_not_count(self):
        bruno = UserFactory()
        bruno_restaurants = ExpenseCategoryFactory(user=bruno, code="restaurants")
        for _ in range(3):
            share = ExpenseShare(
                creator=bruno,
                friends=[self.me],
                description="Shared",
                total=Decimal("10.00"),
                currency=self.euro,
            )
            bruno_participant = create_shared_expense(share)
            ExpenseFactory(
                user=bruno,
                category=bruno_restaurants,
                shared_expense_participant=bruno_participant,
            )
            ExpenseFactory(
                user=self.me,
                category=self.my_food,
                shared_expense_participant=SharedExpenseParticipant.objects.get(
                    shared_expense=bruno_participant.shared_expense, user=self.me
                ),
            )

        suggestion = self.suggestion_for(self.anna_restaurants)

        self.assertIsNone(suggestion)

    def test_inactive_category_is_not_suggested(self):
        self.complete(self.anna_restaurants, self.my_food)
        self.complete(self.anna_restaurants, self.my_food)
        self.complete(self.anna_restaurants, self.my_food)
        self.my_food.is_active = False
        self.my_food.save()

        suggestion = self.suggestion_for(self.anna_restaurants)

        self.assertIsNone(suggestion)

    def test_completed_share_has_no_suggestion(self):
        self.complete(self.anna_restaurants, self.my_food)
        self.complete(self.anna_restaurants, self.my_food)
        self.complete(self.anna_restaurants, self.my_food)
        notification = Notification.objects.filter(user=self.me).latest("id")
        url = reverse("expenses:notifications-detail", args=[notification.id])

        res = self.client.get(url)

        self.assertTrue(res.data["shared_expense"]["is_completed"])
        self.assertIsNone(res.data["shared_expense"]["suggested_category"])
