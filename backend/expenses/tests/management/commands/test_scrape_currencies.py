import datetime as dt
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from expenses.managers.exchange_rate_manager import ExchangeRateError, RateResponse
from expenses.models import DollarExchangeRate
from expenses.tests.factories.currency_factories import CurrencyFactory
from expenses.tests.factories.dollar_exchange_rate_factories import (
    DollarExchangeRateFactory,
)
from expenses import date_utils


class TestScrapeCurrenciesCommand(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usd = CurrencyFactory(
            code="USD", symbol="$", display_name="United States Dollar"
        )
        cls.eur = CurrencyFactory(code="EUR", symbol="€", display_name="Euro")
        cls.uyu = CurrencyFactory(code="UYU", symbol="$", display_name="Uruguayan Peso")

    def test_successful_scraping_when_no_currencies_exist(self):
        """Test successful scraping when no currencies exist for yesterday"""
        yesterday = date_utils.today() - dt.timedelta(days=1)

        # Mock API to return rates for EUR and UYU
        mock_rates = [
            RateResponse(currency_code="EUR", rate=Decimal("0.85"), day=yesterday),
            RateResponse(currency_code="UYU", rate=Decimal("39.5"), day=yesterday),
        ]

        with patch(
            "expenses.managers.exchange_rate_manager.get_exchange_rate_from_api",
            return_value=mock_rates,
        ):
            stdout = StringIO()
            stderr = StringIO()

            call_command("scrape_currencies", stdout=stdout, stderr=stderr)

            output = stdout.getvalue()
            self.assertIn(
                f"Fetching exchange rates for {yesterday.isoformat()}...", output
            )
            self.assertIn(
                f"Successfully scraped and saved exchange rates for {yesterday.isoformat()}",
                output,
            )
            self.assertEqual(stderr.getvalue(), "")

            # Verify rates were saved
            self.assertTrue(
                DollarExchangeRate.objects.filter(
                    currency=self.eur, date=yesterday
                ).exists()
            )
            self.assertTrue(
                DollarExchangeRate.objects.filter(
                    currency=self.uyu, date=yesterday
                ).exists()
            )

    def test_successful_scraping_when_some_currencies_already_exist(self):
        """Test successful scraping when some currencies already exist for yesterday"""
        yesterday = date_utils.today() - dt.timedelta(days=1)

        # Create existing exchange rate for EUR for yesterday
        DollarExchangeRateFactory(
            currency=self.eur, date=yesterday, rate=Decimal("42.0")
        )

        # Mock API to return rates for EUR and UYU (EUR already exists, UYU doesn't)
        mock_rates = [
            RateResponse(currency_code="EUR", rate=Decimal("0.85"), day=yesterday),
            RateResponse(currency_code="UYU", rate=Decimal("39.5"), day=yesterday),
        ]

        with patch(
            "expenses.managers.exchange_rate_manager.get_exchange_rate_from_api",
            return_value=mock_rates,
        ):
            stdout = StringIO()
            stderr = StringIO()

            call_command("scrape_currencies", stdout=stdout, stderr=stderr)

            output = stdout.getvalue()
            self.assertIn(
                f"Fetching exchange rates for {yesterday.isoformat()}...", output
            )
            self.assertIn(
                f"Successfully scraped and saved exchange rates for {yesterday.isoformat()}",
                output,
            )
            self.assertEqual(stderr.getvalue(), "")

            # Verify existing EUR rate is still there with original value
            eur_rate = DollarExchangeRate.objects.get(currency=self.eur, date=yesterday)
            self.assertEqual(eur_rate.rate, Decimal("42.0"))

            # Verify UYU rate was saved (since it didn't exist)
            self.assertTrue(
                DollarExchangeRate.objects.filter(
                    currency=self.uyu, date=yesterday
                ).exists()
            )

    def test_exchange_rate_error_handling(self):
        """Test ExchangeRateError exception handling"""
        error_message = "Failed to fetch exchange rates"

        # Mock save_exchange_rates_to_database to raise ExchangeRateError
        # This simulates an error during the save process
        with patch(
            "expenses.managers.exchange_rate_manager.get_exchange_rate_from_api",
            return_value=[
                RateResponse(
                    currency_code="EUR",
                    rate=Decimal("0.85"),
                    day=date_utils.today() - dt.timedelta(days=1),
                )
            ],
        ):
            with patch(
                "expenses.managers.exchange_rate_manager.save_exchange_rates_to_database",
                side_effect=ExchangeRateError(error_message),
            ):
                stdout = StringIO()
                stderr = StringIO()

                with self.assertRaises(ExchangeRateError):
                    call_command("scrape_currencies", stdout=stdout, stderr=stderr)

                output = stderr.getvalue()
                self.assertIn(f"Exchange rate error: {error_message}", output)

    def test_unexpected_error_handling(self):
        """Test unexpected exception handling"""
        error_message = "Unexpected database error"

        # Mock get_exchange_rate_from_api to raise an unexpected exception
        with patch(
            "expenses.managers.exchange_rate_manager.get_exchange_rate_from_api",
            side_effect=Exception(error_message),
        ):
            stdout = StringIO()
            stderr = StringIO()

            with self.assertRaises(Exception):
                call_command("scrape_currencies", stdout=stdout, stderr=stderr)

            output = stderr.getvalue()
            self.assertIn(
                f"Unexpected error while scraping currencies: {error_message}", output
            )
