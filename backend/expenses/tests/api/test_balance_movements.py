from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from expenses.sharing import ExpenseShare, create_shared_expense
from expenses.tests.api.api_test_case import ApiTestCase
from expenses.tests.factories.currency_factories import CurrencyFactory
from expenses.tests.factories.user_factories import UserFactory
from rest_framework import status


class TestBalanceMovements(ApiTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.euro = CurrencyFactory(code="EUR", symbol="€", display_name="Euro")
        cls.me = UserFactory(first_name="Me", last_name="Myself")
        cls.anna = UserFactory(first_name="Anna", last_name="Rossi")
        cls.bruno = UserFactory(first_name="Bruno", last_name="Verdi")

    def setUp(self):
        self.login(self.me.email)

    def share(self, creator, friends, total, description="Dinner"):
        create_shared_expense(
            ExpenseShare(
                creator=creator,
                friends=friends,
                description=description,
                total=Decimal(total),
                currency=self.euro,
            )
        )

    def share_with_anna(self, descriptions):
        """One shared expense with Anna for each description, oldest first."""
        for description in descriptions:
            self.share(self.me, [self.anna], "10.00", description=description)

    def url(self, person, page=1):
        path = reverse("expenses:balances-movements", args=[person.id])
        return f"{path}?page={page}"

    def movements(self, person, page=1) -> list[tuple[str, str]]:
        res = self.client.get(self.url(person, page))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        return [(m["description"], m["amount"]) for m in res.data["results"]]

    def test_movement_states_description_date_quota_and_currency(self):
        self.share(self.me, [self.anna], "30.00")

        res = self.client.get(self.url(self.anna))

        self.assertEqual(
            res.data["results"],
            [
                {
                    "description": "Dinner",
                    "date": timezone.localdate().isoformat(),
                    "amount": "15.00",
                    "currency": {
                        "id": self.euro.id,
                        "code": "EUR",
                        "symbol": "€",
                        "display_name": "Euro",
                    },
                }
            ],
        )

    def test_movements_in_both_directions_are_listed_newest_first(self):
        self.share(self.me, [self.anna], "30.00", description="Cinema")
        self.share(self.anna, [self.me], "10.00", description="Taxi")

        self.assertEqual(
            self.movements(self.anna), [("Taxi", "-5.00"), ("Cinema", "15.00")]
        )

    def test_movements_with_other_people_are_excluded(self):
        self.share(self.me, [self.anna], "30.00", description="Cinema")
        self.share(self.me, [self.bruno], "30.00", description="Taxi")

        self.assertEqual(self.movements(self.anna), [("Cinema", "15.00")])

    def test_quota_between_two_friends_on_the_same_expense_is_excluded(self):
        self.share(self.anna, [self.me, self.bruno], "30.00")

        self.assertEqual(self.movements(self.bruno), [])

    def test_my_own_quotas_are_not_movements_with_myself(self):
        self.share(self.me, [self.anna], "30.00")

        self.assertEqual(self.movements(self.me), [])

    def test_first_page_holds_the_newest_movements(self):
        self.share_with_anna(["1", "2", "3", "4", "5", "6"])

        res = self.client.get(self.url(self.anna))

        self.assertEqual(res.data["count"], 6)
        self.assertEqual(
            [m["description"] for m in res.data["results"]], ["6", "5", "4", "3", "2"]
        )

    def test_second_page_holds_the_oldest_movements(self):
        self.share_with_anna(["1", "2", "3", "4", "5", "6"])

        self.assertEqual(self.movements(self.anna, page=2), [("1", "5.00")])

    def test_movements_require_authentication(self):
        self.logout()

        res = self.client.get(self.url(self.anna))

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
