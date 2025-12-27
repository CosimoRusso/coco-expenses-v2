import csv
from decimal import Decimal
from functools import reduce
from django.core.management import BaseCommand

from django.conf import settings
from expenses.models.currency import Currency
import datetime as dt
from expenses.models.dollar_exchange_rate import DollarExchangeRate


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("currency_code", type=str)

    def handle(self, *args, **options):
        currency_code = options["currency_code"]
        if not currency_code:
            raise ValueError("Currency code is required")

        currency_code = currency_code.upper()

        if currency_code == "USD":
            raise ValueError("USD is not a valid currency code as all the values are 1")

        currency = Currency.objects.filter(code=currency_code).first()
        if not currency:
            raise ValueError(f"Currency with code {currency_code} not found")

        file_path = f"{settings.BASE_DIR}/expenses/fixtures/historical_timeseries/{currency_code.lower()}.csv"
        with open(file_path, "r") as file:
            reader = csv.reader(file)
            next(reader)  # skip header

            rates = list(reader)
            rates = [
                (dt.datetime.strptime(row[0], "%Y-%m-%d"), Decimal(row[1]))
                for row in rates
            ]

            min_date = reduce(lambda x, y: x if x[0] < y[0] else y, rates)[0]
            max_date = reduce(lambda x, y: x if x[0] > y[0] else y, rates)[0]

            DollarExchangeRate.objects.filter(
                currency=currency, date__gte=min_date, date__lte=max_date
            ).delete()

            rates = [
                DollarExchangeRate(currency=currency, date=date, rate=rate)
                for date, rate in rates
            ]
            DollarExchangeRate.objects.bulk_create(rates)
