from expenses.tests.factories.dollar_exchange_rate_factories import DollarExchangeRateFactory
from django.test import TestCase
from expenses.managers import exchange_rate_manager
from expenses.managers.exchange_rate_manager import RateResponse
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
        self.assertEqual(exchange_rate_manager.convert_to_dollars(100, self.usd, self.today), 100)
        self.assertEqual(exchange_rate_manager.convert_from_dollars(100, self.usd, self.today), 100)
        self.assertEqual(exchange_rate_manager.convert_currency_to_currency(100, self.usd, self.usd, self.today), 100)

    def test_convert_to_dollars_calling_api(self):
        with patch(
            "expenses.managers.exchange_rate_manager.get_exchange_rate_from_api",
            return_value=[RateResponse(
                currency_code="EUR", rate=Decimal(2.0)
            )],
        ) as mock_get_exchange_rate_from_api:
            result = exchange_rate_manager.convert_to_dollars(100, self.eur, self.today)
            mock_get_exchange_rate_from_api.assert_called_once_with(self.today)
            self.assertEqual(result, 50)

    def test_convert_to_dollars_from_db(self):
        DollarExchangeRateFactory(currency=self.eur, date=self.today, rate=Decimal(2.0))
        result = exchange_rate_manager.convert_to_dollars(100, self.eur, self.today)
        self.assertEqual(result, 50)

    def test_convert_from_dollars(self):
        DollarExchangeRateFactory(currency=self.eur, date=self.today, rate=Decimal(40.0))
        result = exchange_rate_manager.convert_from_dollars(1, self.eur, self.today)
        self.assertEqual(result, Decimal(40.0))

    def test_convert_currency_to_currency_from_db(self):
        DollarExchangeRateFactory(currency=self.eur, date=self.today, rate=Decimal(2.0))
        DollarExchangeRateFactory(currency=self.gbp, date=self.today, rate=Decimal(3.0))
        result = exchange_rate_manager.convert_currency_to_currency(30, self.eur, self.gbp, self.today)
        self.assertEqual(result, Decimal(45.0))
