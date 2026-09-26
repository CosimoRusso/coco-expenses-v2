from decimal import Decimal

from django.test import SimpleTestCase
from expenses.sharing import InvalidSplit, check_quotas, split_equally


class TestSplitEqually(SimpleTestCase):
    def test_exact_division_gives_equal_quotas(self):
        self.assertEqual(
            split_equally(Decimal("30.00"), 3),
            [Decimal("10.00"), Decimal("10.00"), Decimal("10.00")],
        )

    def test_leftover_cent_goes_to_first_quota(self):
        self.assertEqual(
            split_equally(Decimal("10.00"), 3),
            [Decimal("3.34"), Decimal("3.33"), Decimal("3.33")],
        )

    def test_leftover_cents_go_to_first_quota(self):
        self.assertEqual(
            split_equally(Decimal("0.05"), 3),
            [Decimal("0.03"), Decimal("0.01"), Decimal("0.01")],
        )

    def test_single_part_keeps_the_total(self):
        self.assertEqual(split_equally(Decimal("12.34"), 1), [Decimal("12.34")])


class TestCheckQuotas(SimpleTestCase):
    """The creator is user 1, sharing 10.00 with users 2 and 3."""

    user_ids = [1, 2, 3]
    total = Decimal("10.00")

    def check(self, quotas: dict[int, str]) -> None:
        split = {user_id: Decimal(quota) for user_id, quota in quotas.items()}
        check_quotas(split, self.user_ids, self.total)

    def test_uneven_quotas_adding_up_to_the_total_are_valid(self):
        self.check({1: "6.00", 2: "3.50", 3: "0.50"})

    def test_a_friend_can_have_a_zero_quota(self):
        self.check({1: "10.00", 2: "0.00", 3: "0.00"})

    def test_quotas_not_adding_up_to_the_total_are_rejected(self):
        with self.assertRaisesMessage(InvalidSplit, "add up to the total of 10.00"):
            self.check({1: "6.00", 2: "3.00", 3: "0.99"})

    def test_a_missing_participant_is_rejected(self):
        with self.assertRaisesMessage(InvalidSplit, "a quota to each participant"):
            self.check({1: "6.00", 2: "4.00"})

    def test_a_quota_for_someone_not_sharing_is_rejected(self):
        with self.assertRaisesMessage(InvalidSplit, "a quota to each participant"):
            self.check({1: "6.00", 2: "2.00", 3: "1.00", 4: "1.00"})

    def test_a_negative_quota_is_rejected(self):
        with self.assertRaisesMessage(InvalidSplit, "cannot be negative"):
            self.check({1: "6.00", 2: "5.00", 3: "-1.00"})

    def test_the_creator_can_have_a_zero_quota(self):
        self.check({1: "0.00", 2: "5.00", 3: "5.00"})
