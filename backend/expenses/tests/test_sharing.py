from decimal import Decimal

from django.test import SimpleTestCase
from expenses.sharing import split_equally


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
