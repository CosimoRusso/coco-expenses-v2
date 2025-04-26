import uuid
from django.db import models

from expenses import date_utils
from expenses.constants import TOKEN_DURATION
import datetime as dt


class Token(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    expiration_date = models.DateTimeField(null=True)

    def extend_expiration_date(self) -> None:
        new_expiration = self.get_extended_expiration_date()
        if new_expiration:
            self.expiration_date = new_expiration
            self.save(update_fields=["expiration_date"])
        return None

    def get_extended_expiration_date(self) -> dt.datetime | None:
        if not self.expiration_date:
            return None  # No need to do it
        return max(self.expiration_date, date_utils.now() + TOKEN_DURATION)
