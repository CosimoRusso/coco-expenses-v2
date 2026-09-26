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

    def share(self, creator, friends, total, currency=None, description="Dinner"):
        create_shared_expense(
            ExpenseShare(
                creator=creator,
                friends=friends,
                description=description,
                total=Decimal(total),
                currency=currency or self.euro,
            )
        )

    def balances(self) -> dict[int, str]:
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        return {b["user_id"]: b["amount"] for b in res.data["balances"]}

    def share_with_anna(self, descriptions):
        """One shared expense with Anna for each description, oldest first."""
        for description in descriptions:
            self.share(self.me, [self.anna], "10.00", description=description)

    def movements(self) -> dict[int, list[dict]]:
        res = self.client.get(self.url)
        return {b["user_id"]: b["movements"] for b in res.data["balances"]}

    def descriptions(self) -> dict[int, list[str]]:
        return {
            user_id: [m["description"] for m in movements]
            for user_id, movements in self.movements().items()
        }

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

    def test_movement_i_paid_shows_the_quota_the_friend_owes_me(self):
        self.share(self.me, [self.anna], "30.00", currency=self.dollar)

        self.assertEqual(
            self.movements()[self.anna.id],
            [
                {
                    "description": "Dinner",
                    "date": timezone.localdate().isoformat(),
                    "amount": "15.00",
                    "currency": {
                        "id": self.dollar.id,
                        "code": "USD",
                        "symbol": "$",
                        "display_name": "Dollar",
                    },
                }
            ],
        )

    def test_movement_a_friend_paid_shows_my_quota_as_negative(self):
        self.share(self.anna, [self.me, self.bruno], "30.00")

        self.assertEqual(self.movements()[self.anna.id][0]["amount"], "-10.00")

    def test_movements_are_listed_under_the_person_they_are_shared_with(self):
        self.share(self.me, [self.anna], "10.00", description="Cinema")
        self.share(self.bruno, [self.me], "10.00", description="Taxi")

        self.assertEqual(
            self.descriptions(), {self.anna.id: ["Cinema"], self.bruno.id: ["Taxi"]}
        )

    def test_movements_are_newest_first(self):
        self.share(self.me, [self.anna], "10.00", description="Cinema")
        self.share(self.anna, [self.me], "10.00", description="Taxi")

        self.assertEqual(self.descriptions()[self.anna.id], ["Taxi", "Cinema"])

    def test_only_the_latest_ten_movements_are_listed(self):
        self.share_with_anna(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"])

        self.assertEqual(
            self.descriptions()[self.anna.id],
            ["11", "10", "9", "8", "7", "6", "5", "4", "3", "2"],
        )

    def test_balance_counts_movements_beyond_the_latest_ten(self):
        self.share_with_anna(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"])

        self.assertEqual(self.balances(), {self.anna.id: "55.00"})
