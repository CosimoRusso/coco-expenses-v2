from django.core.management import BaseCommand

from expenses.models.user import get_hashed_password, User


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("email", type=str)
        parser.add_argument("password", type=str)

    def handle(self, *args, **options):
        email = options["email"]
        password = options["password"]
        password_hash = get_hashed_password(password)

        u = User.objects.get(email=email)
        u.password_hash = password_hash
        u.save(update_fields=["password_hash"])
