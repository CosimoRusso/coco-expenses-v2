import datetime as dt

from dateutil.relativedelta import relativedelta
from django.db import models
from expenses import date_utils


class UserSettings(models.Model):
    user = models.OneToOneField(
        "User",
        on_delete=models.PROTECT,
    )
    preferred_currency = models.ForeignKey(
        "Currency",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    active_trip = models.ForeignKey(
        "Trip",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    is_encrypted = models.BooleanField(default=False)
    default_statistics_start_date = models.DateField(null=True, blank=True)
    default_statistics_end_date = models.DateField(null=True, blank=True)

    @property
    def statistics_start_date(self) -> dt.date:
        """The first day of the period the statistics page opens on."""
        if self.default_statistics_start_date:
            return self.default_statistics_start_date
        return date_utils.today() - relativedelta(months=6)

    @property
    def statistics_end_date(self) -> dt.date:
        """The last day of the period the statistics page opens on."""
        return self.default_statistics_end_date or date_utils.today()
