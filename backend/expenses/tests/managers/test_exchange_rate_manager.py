from expenses.tests.factories.dollar_exchange_rate_factories import (
    DollarExchangeRateFactory,
)
from django.test import TestCase
from expenses.managers import exchange_rate_manager
from expenses.managers.exchange_rate_manager import Money, RateResponse
import datetime as dt
from unittest.mock import patch
from expenses.tests.factories.currency_factories import CurrencyFactory
from decimal import Decimal


class ExchangeRateManagerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usd = CurrencyFactory(
            code="USD", symbol="$", display_name="United States Dollar"
        )
        cls.eur = CurrencyFactory(code="EUR", symbol="€", display_name="Euro")
        cls.gbp = CurrencyFactory(code="GBP", symbol="£", display_name="Pound Sterling")
        cls.today = dt.date.today()

    def test_convert_dollars_to_dollars(self):
        self.assertEqual(
            exchange_rate_manager.convert_to_dollars(100, self.usd, self.today), 100
        )
        self.assertEqual(
            exchange_rate_manager.convert_from_dollars(100, self.usd, self.today), 100
        )
        self.assertEqual(
            exchange_rate_manager.convert_currency_to_currency(
                100, self.usd, self.usd, self.today
            ),
            100,
        )

    def test_convert_to_dollars_calling_api(self):
        with patch(
            "expenses.managers.exchange_rate_manager.get_exchange_rate_from_api",
            return_value=[RateResponse(currency_code="EUR", rate=Decimal(2.0))],
        ) as mock_get_exchange_rate_from_api:
            result = exchange_rate_manager.convert_to_dollars(100, self.eur, self.today)
            mock_get_exchange_rate_from_api.assert_called_once_with(self.today)
            self.assertEqual(result, 50)

    def test_convert_to_dollars_from_db(self):
        DollarExchangeRateFactory(currency=self.eur, date=self.today, rate=Decimal(2.0))
        result = exchange_rate_manager.convert_to_dollars(100, self.eur, self.today)
        self.assertEqual(result, 50)

    def test_convert_from_dollars(self):
        DollarExchangeRateFactory(
            currency=self.eur, date=self.today, rate=Decimal(40.0)
        )
        result = exchange_rate_manager.convert_from_dollars(1, self.eur, self.today)
        self.assertEqual(result, Decimal(40.0))

    def test_convert_currency_to_currency_from_db(self):
        DollarExchangeRateFactory(currency=self.eur, date=self.today, rate=Decimal(2.0))
        DollarExchangeRateFactory(currency=self.gbp, date=self.today, rate=Decimal(3.0))
        result = exchange_rate_manager.convert_currency_to_currency(
            30, self.eur, self.gbp, self.today
        )
        self.assertEqual(result, Decimal(45.0))

    @patch("expenses.managers.exchange_rate_manager.get_exchange_rate_from_api")
    def test_bulk_convert_dollars_to_dollars(self, mock_get_exchange_rate_from_api):
        result = exchange_rate_manager.bulk_convert_to_currency(
            [Money(amount=100, currency=self.usd, day=self.today)], self.usd
        )
        mock_get_exchange_rate_from_api.assert_not_called()
        self.assertEqual(result, [Money(amount=100, currency=self.usd, day=self.today)])

    def test_bulk_convert_to_currency(self):
        self.maxDiff = None
        input = [
            Money(amount=100, currency=self.usd, day=self.today),
            Money(amount=10, currency=self.eur, day=self.today),
            Money(amount=10, currency=self.gbp, day=self.today),
            Money(amount=10, currency=self.usd, day=self.today),
            Money(amount=100, currency=self.eur, day=self.today),
        ]
        DollarExchangeRateFactory(currency=self.eur, date=self.today, rate=Decimal(0.5))
        DollarExchangeRateFactory(
            currency=self.gbp, date=self.today, rate=Decimal(0.25)
        )

        expected = [
            Money(amount=50, currency=self.eur, day=self.today),
            Money(amount=10, currency=self.eur, day=self.today),
            Money(amount=20, currency=self.eur, day=self.today),
            Money(amount=5, currency=self.eur, day=self.today),
            Money(amount=100, currency=self.eur, day=self.today),
        ]
        result = exchange_rate_manager.bulk_convert_to_currency(input, self.eur)

        self.assertEqual(result, expected)
