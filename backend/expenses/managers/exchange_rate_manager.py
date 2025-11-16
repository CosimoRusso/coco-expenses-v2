from dataclasses import dataclass
from decimal import Decimal
from expenses.models import Currency, DollarExchangeRate
import datetime as dt
from django.conf import settings
import requests
from typing import Literal

__all__ = ["convert_to_dollars", "convert_from_dollars", "convert_currency_to_currency", "ExchangeRateError"]

MAX_RETRIES = 3

class ExchangeRateError(Exception):
    pass

@dataclass
class RateResponse:
    currency_code: str
    rate: Decimal

def convert_to_dollars(amount: Decimal, currency: Currency, day: dt.date) -> Decimal:
    return _convert_dollars(amount, currency, day, "to_dollars")

def convert_from_dollars(amount: Decimal, currency: Currency, day: dt.date) -> Decimal:
    return _convert_dollars(amount, currency, day, "from_dollars")

def convert_currency_to_currency(amount: Decimal, from_currency: Currency, to_currency: Currency, day: dt.date) -> Decimal:
    if from_currency.code == to_currency.code:
        return amount
    dollars_amount = convert_to_dollars(amount, from_currency, day)
    return convert_from_dollars(dollars_amount, to_currency, day)

def _convert_dollars(amount: Decimal, currency: Currency, day: dt.date, direction: Literal["to_dollars", "from_dollars"]) -> Decimal:
    if currency.code == "USD":
        return amount
    _day = day if day <= dt.date.today() else dt.date.today()
    exchange_rate = get_exchange_rate_for_day(_day, currency)
    if direction == "to_dollars":
        return amount / exchange_rate.rate
    else:
        return amount * exchange_rate.rate

def get_exchange_rate_for_day(day: dt.date, currency: Currency) -> DollarExchangeRate:
    exchange_rate = DollarExchangeRate.objects.filter(currency=currency, date=day).first()
    if not exchange_rate:
        try:
            get_exchange_rates_from_api_and_save_to_database(day)
        except Exception as e:
            raise ExchangeRateError(f"Failed to get exchange rate from API: {e}")
        exchange_rate = DollarExchangeRate.objects.filter(currency=currency, date=day).first()
    if not exchange_rate:
        raise ExchangeRateError(f"No exchange rate found for {currency} on {day}")
    return exchange_rate

def get_exchange_rate_from_api(day: dt.date) -> list[RateResponse]:
    """ Get the exchange rate from the Open Exchange Rates API for all currencies"""
    day_str = day.isoformat()
    app_id = settings.OPENEXCHANGERATES_APP_ID
    if not app_id:
        raise ValueError("OPENEXCHANGERATES_APP_ID is not set")
    url = f"https://openexchangerates.org/api/historical/{day_str}.json?app_id={app_id}"
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"Failed to get exchange rate from API: {response.status_code} {response.text}")
    data = response.json()
    return [RateResponse(currency_code=currency_code, rate=Decimal(rate)) for currency_code, rate in data["rates"].items()]

def save_exchange_rates_to_database(rates: list[RateResponse], day: dt.date):
    available_currencies = Currency.objects.all()
    rates_to_save = []
    for currency in available_currencies:
        rate = next((rate for rate in rates if rate.currency_code == currency.code), None)
        if rate:
            rates_to_save.append(DollarExchangeRate(currency=currency, date=day, rate=rate.rate))
    DollarExchangeRate.objects.bulk_create(rates_to_save)

def get_exchange_rates_from_api_and_save_to_database(day: dt.date):
    rates = get_exchange_rate_from_api(day)
    save_exchange_rates_to_database(rates, day)