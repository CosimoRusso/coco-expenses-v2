import datetime as dt
from decimal import Decimal
from unittest.mock import patch

from django.core.management import CommandError, call_command
from django.test import TestCase
from expenses import favourite_currency_cache
from expenses.favourite_currency_cache import (
    MissingCryptoKey,
    populate_favourite_currency_amounts,
    populate_in_batches,
)
from expenses.tests.factories.category_factories import CategoryFactory
from expenses.tests.factories.currency_factories import CurrencyFactory
from expenses.tests.factories.dollar_exchange_rate_factories import (
    DollarExchangeRateFactory,
)
from expenses.tests.factories.expense_factories import ExpenseFactory
from expenses.tests.factories.user_factories import UserFactory
from expenses.tests.factories.user_settings_factories import UserSettingsFactory
from expenses.utils.encryption.encryption import (
    decrypt_text_with_password,
    encrypt_user_data,
)

DAY = dt.date(2025, 3, 10)


class FavouriteCurrencyCacheTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.euro = CurrencyFactory(code="EUR")
        cls.dollar = CurrencyFactory(code="USD")
        cls.pound = CurrencyFactory(code="GBP")
        cls.user_settings = UserSettingsFactory(
            user=cls.user, preferred_currency=cls.euro
        )
        cls.category = CategoryFactory(user=cls.user, for_expense=True)
        DollarExchangeRateFactory(currency=cls.euro, date=DAY, rate=Decimal("0.5"))
        DollarExchangeRateFactory(currency=cls.pound, date=DAY, rate=Decimal("0.4"))

    def expense(self, **fields):
        defaults = {
            "user": self.user,
            "category": self.category,
            "currency": self.dollar,
            "expense_date": DAY,
            "amount": Decimal("10.00"),
        }
        return ExpenseFactory(**{**defaults, **fields})

    def test_converts_from_dollars_at_the_rate_of_the_expense_date(self):
        expense = self.expense(amount=Decimal("10.00"), currency=self.dollar)

        populate_favourite_currency_amounts(self.user)

        expense.refresh_from_db()
        self.assertEqual(expense.amount_favourite_currency, Decimal("5.00"))

    def test_converts_between_two_currencies_through_dollars(self):
        expense = self.expense(amount=Decimal("10.00"), currency=self.pound)

        populate_favourite_currency_amounts(self.user)

        expense.refresh_from_db()
        self.assertEqual(expense.amount_favourite_currency, Decimal("12.50"))

    def test_rounds_the_converted_amount_half_up_to_cents(self):
        expense = self.expense(amount=Decimal("0.01"), currency=self.dollar)

        populate_favourite_currency_amounts(self.user)

        expense.refresh_from_db()
        self.assertEqual(expense.amount_favourite_currency, Decimal("0.01"))

    def test_keeps_the_amount_of_an_expense_already_in_the_favourite_currency(self):
        expense = self.expense(amount=Decimal("7.30"), currency=self.euro)

        populate_favourite_currency_amounts(self.user)

        expense.refresh_from_db()
        self.assertEqual(expense.amount_favourite_currency, Decimal("7.30"))

    def test_does_not_convert_again_an_expense_already_converted(self):
        expense = self.expense(amount_favourite_currency=Decimal("99.00"))

        converted = populate_favourite_currency_amounts(self.user)

        expense.refresh_from_db()
        self.assertEqual(converted, 0)
        self.assertEqual(expense.amount_favourite_currency, Decimal("99.00"))

    def test_leaves_the_expenses_of_other_users_alone(self):
        other = self.expense(user=UserFactory())

        populate_favourite_currency_amounts(self.user)

        other.refresh_from_db()
        self.assertIsNone(other.amount_favourite_currency)

    def test_skips_an_expense_without_amount(self):
        self.expense(amount=None)

        converted = populate_favourite_currency_amounts(self.user)

        self.assertEqual(converted, 0)

    def test_skips_an_expense_without_currency(self):
        self.expense(currency=None)

        converted = populate_favourite_currency_amounts(self.user)

        self.assertEqual(converted, 0)

    def test_saves_the_expenses_one_batch_at_a_time(self):
        self.expense()
        self.expense()
        self.expense()

        with patch.object(favourite_currency_cache, "BATCH_SIZE", 2):
            batch_sizes = list(populate_in_batches(self.user))

        self.assertEqual(batch_sizes, [2, 1])

    def test_keeps_the_batches_converted_before_an_interruption(self):
        first = self.expense()
        second = self.expense()
        third = self.expense()

        with patch.object(favourite_currency_cache, "BATCH_SIZE", 2):
            next(populate_in_batches(self.user))

        first.refresh_from_db()
        second.refresh_from_db()
        third.refresh_from_db()
        self.assertEqual(first.amount_favourite_currency, Decimal("5.00"))
        self.assertEqual(second.amount_favourite_currency, Decimal("5.00"))
        self.assertIsNone(third.amount_favourite_currency)

    def test_encrypted_user_gets_the_converted_amount_encrypted(self):
        expense = self.expense(amount=Decimal("10.00"), currency=self.dollar)
        self.encrypt("password")

        call_command(
            "populate_favourite_currency_amounts", self.user.id, password="password"
        )

        expense.refresh_from_db()
        self.assertIsNone(expense.amount_favourite_currency)
        self.assertEqual(
            decrypt_text_with_password(
                self.user, "password", expense.encrypted_amount_favourite_currency
            ),
            "5.00",
        )

    def test_encrypting_drops_the_amount_converted_in_plain_text(self):
        expense = self.expense(amount_favourite_currency=Decimal("5.00"))

        self.encrypt("password")

        expense.refresh_from_db()
        self.assertIsNone(expense.amount_favourite_currency)
        self.assertEqual(expense.encrypted_amount_favourite_currency, "")

    def test_encrypted_user_cannot_be_converted_without_crypto_key(self):
        self.expense()
        self.encrypt("password")

        with self.assertRaises(MissingCryptoKey):
            populate_favourite_currency_amounts(self.user)

    def test_command_converts_the_expenses_of_the_user(self):
        expense = self.expense(amount=Decimal("10.00"), currency=self.dollar)

        call_command("populate_favourite_currency_amounts", self.user.id)

        expense.refresh_from_db()
        self.assertEqual(expense.amount_favourite_currency, Decimal("5.00"))

    def test_command_asks_for_the_password_of_an_encrypted_user(self):
        self.expense()
        self.encrypt("password")

        with self.assertRaisesMessage(CommandError, "pass --password"):
            call_command("populate_favourite_currency_amounts", self.user.id)

    def test_command_rejects_an_unknown_user(self):
        with self.assertRaisesMessage(CommandError, "No user with id 0"):
            call_command("populate_favourite_currency_amounts", 0)

    def encrypt(self, password: str) -> None:
        self.user_settings.is_encrypted = True
        self.user_settings.save()
        encrypt_user_data(self.user, password)
