from django.core.management import BaseCommand
from django.db import IntegrityError

from expenses.models.currency import Currency


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("code", type=str, help="ISO-style currency code (e.g. USD)")
        parser.add_argument("symbol", type=str, help="Display symbol (e.g. $)")
        parser.add_argument("display_name", type=str, help="Human-readable name")

    def handle(self, *args, **options):
        code = options["code"].strip().upper()
        symbol = options["symbol"].strip()
        display_name = options["display_name"].strip()

        try:
            Currency.objects.create(
                code=code,
                symbol=symbol,
                display_name=display_name,
            )
        except IntegrityError:
            self.stderr.write(
                self.style.ERROR(f'Currency with code "{code}" already exists.')
            )
            raise SystemExit(1)

        self.stdout.write(
            self.style.SUCCESS(f'Created currency {code} ({display_name}).')
        )
