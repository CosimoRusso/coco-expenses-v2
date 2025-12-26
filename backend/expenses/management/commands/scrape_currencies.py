import datetime as dt
from django.core.management import BaseCommand

from expenses.managers.exchange_rate_manager import (
    get_exchange_rates_from_api_and_save_to_database,
    ExchangeRateError,
)
from expenses import date_utils


class Command(BaseCommand):
    help = "Scrapes exchange rates for yesterday from Open Exchange Rates API and saves them to the database"

    def handle(self, *args, **options):
        yesterday = date_utils.today() - dt.timedelta(days=1)
        
        self.stdout.write(f"Fetching exchange rates for {yesterday.isoformat()}...")
        
        try:
            get_exchange_rates_from_api_and_save_to_database(yesterday)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully scraped and saved exchange rates for {yesterday.isoformat()}"
                )
            )
        except ExchangeRateError as e:
            self.stderr.write(
                self.style.ERROR(f"Exchange rate error: {e}")
            )
            raise
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"Unexpected error while scraping currencies: {e}")
            )
            raise

