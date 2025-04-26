from django.core.management import BaseCommand

from expenses.models.user import get_hashed_password, User


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("email", type=str)
        parser.add_argument("password", type=str)
        parser.add_argument("firstname", type=str)
        parser.add_argument("lastname", type=str)

    def handle(self, *args, **options):
        email = options["email"]
        password = options["password"]
        first_name = options["firstname"]
        last_name = options["lastname"]
        password_hash = get_hashed_password(password)

        User.objects.create(
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
        )
