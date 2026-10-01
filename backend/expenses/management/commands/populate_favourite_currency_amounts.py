from django.core.management import BaseCommand, CommandError
from expenses.favourite_currency_cache import MissingCryptoKey, populate_in_batches
from expenses.models.user import User
from expenses.utils.encryption.encryption import derive_key_from_password


class Command(BaseCommand):
    help = "Convert to the favourite currency the expenses of a user not converted yet"

    def add_arguments(self, parser):
        parser.add_argument("user_id", type=int)
        parser.add_argument(
            "--password",
            help="Password of the user, required when their data is encrypted",
        )

    def handle(self, *args, **options):
        user = _user(options["user_id"])
        password = options["password"]
        crypto_key = password and derive_key_from_password(password, user.id)
        converted = 0
        try:
            for batch_size in populate_in_batches(user, crypto_key):
                converted += batch_size
                self.stdout.write(f"Converted {converted} expenses")
        except MissingCryptoKey:
            raise CommandError("The data of this user is encrypted: pass --password")
        self.stdout.write(f"Done: {converted} expenses converted")


def _user(user_id: int) -> User:
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise CommandError(f"No user with id {user_id}")
