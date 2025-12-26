from dataclasses import dataclass
from decimal import Decimal

from django.db.models import Subquery
from expenses.models import Currency, DollarExchangeRate
import datetime as dt
from django.conf import settings
import requests
from typing import Literal
from expenses import utils

__all__ = [
    "convert_to_dollars",
    "convert_from_dollars",
    "convert_currency_to_currency",
    "Money",
    "ExchangeRateError",
    "bulk_convert_to_dollars",
    "bulk_convert_from_dollars",
    "bulk_convert_to_currency",
]

MAX_RETRIES = 3


class ExchangeRateError(Exception):
    pass


@dataclass
class RateResponse:
    currency_code: str
    rate: Decimal
    day: dt.date


@dataclass
class Money:
    amount: Decimal
    currency: Currency
    day: dt.date


def convert_to_dollars(amount: Decimal, currency: Currency, day: dt.date) -> Decimal:
    return _convert_dollars(amount, currency, day, "to_dollars")


def convert_from_dollars(amount: Decimal, currency: Currency, day: dt.date) -> Decimal:
    return _convert_dollars(amount, currency, day, "from_dollars")


def convert_currency_to_currency(
    amount: Decimal, from_currency: Currency, to_currency: Currency, day: dt.date
) -> Decimal:
    if from_currency.code == to_currency.code:
        return amount
    dollars_amount = convert_to_dollars(amount, from_currency, day)
    return convert_from_dollars(dollars_amount, to_currency, day)


def bulk_convert_to_currency(
    money: list[Money], destination_currency: Currency
) -> list[Money]:
    if destination_currency.code == "USD":
        return bulk_convert_to_dollars(money)

    entries_in_usd = [entry for entry in money if entry.currency.code == "USD"]
    entries_already_in_currency = [
        entry for entry in money if entry.currency.code == destination_currency.code
    ]
    other_entries = [
        entry
        for entry in money
        if entry.currency.code != destination_currency.code
        and entry.currency.code != "USD"
    ]

    other_entries_in_usd = bulk_convert_to_dollars(other_entries)
    all_entries_in_usd = entries_in_usd + other_entries_in_usd
    all_entries_in_destination_currency = bulk_convert_from_dollars(
        all_entries_in_usd, destination_currency
    )
    return entries_already_in_currency + all_entries_in_destination_currency


def bulk_convert_to_dollars(money: list[Money]) -> list[Money]:
    today = dt.date.today()
    entries_in_usd = [entry for entry in money if entry.currency.code == "USD"]
    other_entries = [entry for entry in money if entry.currency.code != "USD"]

    converted, not_converted = bulk_convert_to_dollars_from_db(other_entries)

    if len(not_converted) > 0:
        all_unconverted_days = set(min(entry.day, today) for entry in not_converted)
        bulk_get_exchange_rates_from_api_and_save_to_database(all_unconverted_days)

        converted_1, not_converted = bulk_convert_to_dollars_from_db(not_converted)
        converted += converted_1

    if len(not_converted) > 0:
        raise ExchangeRateError("Failed to convert some money to dollars")

    return converted + entries_in_usd


def bulk_convert_from_dollars(
    money: list[Money], destination_currency: Currency
) -> list[Money]:
    today = dt.date.today()
    converted, not_converted = bulk_convert_from_dollars_from_db(
        money, destination_currency
    )

    if len(not_converted) > 0:
        all_unconverted_days = set(min(entry.day, today) for entry in not_converted)
        bulk_get_exchange_rates_from_api_and_save_to_database(all_unconverted_days)

        converted_1, not_converted = bulk_convert_from_dollars_from_db(
            not_converted, destination_currency
        )
        converted += converted_1

    if len(not_converted) > 0:
        raise ExchangeRateError("Failed to convert some money from dollars")

    return converted


def bulk_convert_to_dollars_from_db(
    money: list[Money],
) -> tuple[list[Money], list[Money]]:
    entries_in_usd = [entry for entry in money if entry.currency.code == "USD"]
    other_entries = [entry for entry in money if entry.currency.code != "USD"]
    today = dt.date.today()
    all_days = set(money.day if money.day <= today else today for money in money)
    all_currencies = set(money.currency for money in money)
    rates = DollarExchangeRate.objects.filter(
        currency__in=all_currencies, date__in=all_days
    ).all()

    converted = []
    not_converted = []
    for entry in other_entries:
        day = entry.day if entry.day <= today else today
        currency = entry.currency

        exchange_rate = utils.find_first(
            rates, lambda rate: rate.currency == currency and rate.date == day
        )
        if exchange_rate:
            converted.append(
                Money(
                    amount=entry.amount / exchange_rate.rate,
                    currency=currency,
                    day=entry.day,
                )
            )
        else:
            not_converted.append(entry)

    return converted + entries_in_usd, not_converted


def bulk_convert_from_dollars_from_db(
    money: list[Money], target_currency: Currency
) -> tuple[list[Money], list[Money]]:
    today = dt.date.today()
    all_days = set(money.day if money.day <= today else today for money in money)
    rates = DollarExchangeRate.objects.filter(
        currency=target_currency, date__in=all_days
    ).all()

    converted = []
    not_converted = []
    for entry in money:
        day = min(entry.day, today)

        exchange_rate = utils.find_first(
            rates, lambda rate: rate.currency == target_currency and rate.date == day
        )
        if exchange_rate:
            converted.append(
                Money(
                    amount=entry.amount * exchange_rate.rate,
                    currency=target_currency,
                    day=entry.day,
                )
            )
        else:
            not_converted.append(entry)

    return converted, not_converted


def _convert_dollars(
    amount: Decimal,
    currency: Currency,
    day: dt.date,
    direction: Literal["to_dollars", "from_dollars"],
) -> Decimal:
    if currency.code == "USD":
        return amount
    _day = day if day <= dt.date.today() else dt.date.today()
    exchange_rate = get_exchange_rate_for_day(_day, currency)
    if direction == "to_dollars":
        return amount / exchange_rate.rate
    else:
        return amount * exchange_rate.rate


def get_exchange_rate_for_day(day: dt.date, currency: Currency) -> DollarExchangeRate:
    exchange_rate = DollarExchangeRate.objects.filter(
        currency=currency, date=day
    ).first()
    if not exchange_rate:
        try:
            get_exchange_rates_from_api_and_save_to_database(day)
        except Exception as e:
            raise ExchangeRateError(f"Failed to get exchange rate from API: {e}")
        exchange_rate = DollarExchangeRate.objects.filter(
            currency=currency, date=day
        ).first()
    if not exchange_rate:
        raise ExchangeRateError(f"No exchange rate found for {currency} on {day}")
    return exchange_rate


def get_exchange_rate_from_api(day: dt.date) -> list[RateResponse]:
    """Get the exchange rate from the Open Exchange Rates API for all currencies"""
    day_str = day.isoformat()
    app_id = settings.OPENEXCHANGERATES_APP_ID
    if not app_id:
        raise ValueError("OPENEXCHANGERATES_APP_ID is not set")
    url = f"https://openexchangerates.org/api/historical/{day_str}.json?app_id={app_id}"
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(
            f"Failed to get exchange rate from API: {response.status_code} {response.text}"
        )
    data = response.json()
    return [
        RateResponse(currency_code=currency_code, rate=Decimal(rate), day=day)
        for currency_code, rate in data["rates"].items()
    ]


def bulk_get_exchange_rate_from_api(days: list[dt.date]) -> list[RateResponse]:
    rates = []
    for day in days:
        rates.extend(get_exchange_rate_from_api(day))
    return rates


def save_exchange_rates_to_database(rates: list[RateResponse]):
    available_currencies = Currency.objects.exclude(code="USD").order_by('code')
    rates_to_save = []
    for currency in available_currencies:
        rate = next(
            (rate for rate in rates if rate.currency_code == currency.code), None
        )
        if rate:
            rates_to_save.append(
                DollarExchangeRate(currency=currency, date=rate.day, rate=rate.rate)
            )
    DollarExchangeRate.objects.bulk_create(rates_to_save)


def get_exchange_rates_from_api_and_save_to_database(day: dt.date):
    rates = get_exchange_rate_from_api(day)
    save_exchange_rates_to_database(rates)

def get_exchange_rates_from_api_and_save_to_database_if_not_exists(day: dt.date):
    rates = get_exchange_rate_from_api(day)
    currencies_to_save = Currency.objects.exclude(code="USD").exclude(id__in=Subquery(DollarExchangeRate.objects.filter(date=day).values('currency_id')))
    rates_to_save = list(filter(lambda rate: rate.currency_code in [c.code for c in currencies_to_save], rates))
    save_exchange_rates_to_database(rates_to_save)


def bulk_get_exchange_rates_from_api_and_save_to_database(days: list[dt.date]):
    rates = bulk_get_exchange_rate_from_api(days)
    save_exchange_rates_to_database(rates)
