from django.core.management import BaseCommand

from expenses.models.user import User
from expenses import date_utils


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("email", type=str)

    def handle(self, *args, **options):
        email = options["email"]

        u = User.objects.get(email=email)
        u.email_confirmed_at = date_utils.now()
        u.save(update_fields=["email_confirmed_at"])
