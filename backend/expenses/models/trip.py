from django.db import models

from expenses.models.timestamp import TimestampModel
from expenses.models.user import User


class Trip(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="trips")
    code = models.CharField(verbose_name="Trip Code", max_length=128)
    name = models.CharField(verbose_name="Trip Name", max_length=128)
    is_active = models.BooleanField(verbose_name="Is Active", default=True)

    class Meta:
        unique_together = ("user", "code")
