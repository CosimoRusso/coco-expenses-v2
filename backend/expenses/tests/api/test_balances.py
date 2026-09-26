from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from expenses.models import UserSettings
from expenses.sharing import ExpenseShare, create_shared_expense
from expenses.tests.api.api_test_case import ApiTestCase
from expenses.tests.factories.currency_factories import CurrencyFactory
from expenses.tests.factories.dollar_exchange_rate_factories import (
    DollarExchangeRateFactory,
)
from expenses.tests.factories.user_factories import UserFactory
from rest_framework import status


class TestBalances(ApiTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("expenses:balances-list")
        cls.euro = CurrencyFactory(code="EUR", symbol="€", display_name="Euro")
        cls.dollar = CurrencyFactory(code="USD", symbol="$", display_name="Dollar")
        cls.me = UserFactory(first_name="Me", last_name="Myself")
        cls.anna = UserFactory(first_name="Anna", last_name="Rossi")
        cls.bruno = UserFactory(first_name="Bruno", last_name="Verdi")
        cls.carla = UserFactory(first_name="Carla", last_name="Neri")
        UserSettings.objects.create(user=cls.me, preferred_currency=cls.euro)

    def setUp(self):
        self.login(self.me.email)

    def share(self, creator, friends, total, currency=None):
        create_shared_expense(
            ExpenseShare(
                creator=creator,
                friends=friends,
                description="Dinner",
                total=Decimal(total),
                currency=currency or self.euro,
            )
        )

    def balances(self) -> dict[int, str]:
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        return {b["user_id"]: b["amount"] for b in res.data["balances"]}

    def test_friends_owe_me_their_quota_of_what_i_paid(self):
        self.share(self.me, [self.anna, self.bruno], "30.00")

        self.assertEqual(
            self.balances(), {self.anna.id: "10.00", self.bruno.id: "10.00"}
        )

    def test_i_owe_my_quota_of_what_a_friend_paid(self):
        self.share(self.anna, [self.me, self.bruno], "30.00")

        self.assertEqual(self.balances(), {self.anna.id: "-10.00"})

    def test_debts_in_both_directions_are_netted(self):
        self.share(self.me, [self.anna], "30.00")
        self.share(self.anna, [self.me], "10.00")

        self.assertEqual(self.balances(), {self.anna.id: "10.00"})

    def test_settled_person_is_listed_with_zero(self):
        self.share(self.me, [self.anna], "10.00")
        self.share(self.anna, [self.me], "10.00")

        self.assertEqual(self.balances(), {self.anna.id: "0.00"})

    def test_shared_expenses_i_am_not_part_of_are_ignored(self):
        self.share(self.anna, [self.bruno, self.carla], "30.00")

        self.assertEqual(self.balances(), {})

    def test_balances_are_ordered_by_name(self):
        self.share(self.me, [self.carla, self.anna, self.bruno], "40.00")

        res = self.client.get(self.url)

        self.assertEqual(
            [b["first_name"] for b in res.data["balances"]], ["Anna", "Bruno", "Carla"]
        )

    def test_quotas_are_converted_at_the_rate_of_the_creation_day(self):
        DollarExchangeRateFactory(
            currency=self.euro, date=timezone.localdate(), rate=Decimal("0.5")
        )
        self.share(self.anna, [self.me], "20.00", currency=self.dollar)

        self.assertEqual(self.balances(), {self.anna.id: "-5.00"})

    def test_converted_balance_is_rounded_to_cents(self):
        DollarExchangeRateFactory(
            currency=self.euro, date=timezone.localdate(), rate=Decimal("0.3")
        )
        self.share(self.me, [self.anna], "2.22", currency=self.dollar)

        self.assertEqual(self.balances(), {self.anna.id: "0.33"})

    def test_response_states_the_favourite_currency(self):
        res = self.client.get(self.url)

        self.assertEqual(
            res.data["currency"],
            {"id": self.euro.id, "code": "EUR", "symbol": "€", "display_name": "Euro"},
        )

    def test_currency_defaults_to_dollars_without_a_favourite(self):
        self.login(self.anna.email)

        res = self.client.get(self.url)

        self.assertEqual(res.data["currency"]["code"], "USD")

    def test_balances_require_authentication(self):
        self.logout()

        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
