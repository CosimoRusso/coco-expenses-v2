import datetime as dt

from dateutil.relativedelta import relativedelta
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from expenses import date_utils
from expenses.models.currency import Currency
from expenses.models.timestamp import TimestampModel
from expenses.models.trip import Trip
from expenses.models.user import User

DEFAULT_STATISTICS_N_DAYS_AGO_FROM = 180
DEFAULT_STATISTICS_N_DAYS_AGO_TO = 0
# Keeps today minus the offset inside the range dt.date can represent.
MAX_STATISTICS_DAYS_OFFSET = 36500
STATISTICS_DAYS_OFFSET_VALIDATORS = [
    MinValueValidator(-MAX_STATISTICS_DAYS_OFFSET),
    MaxValueValidator(MAX_STATISTICS_DAYS_OFFSET),
]


class DefaultStatisticsMethod(models.TextChoices):
    HARDCODED_DATES = "HARDCODED_DATES", "Hardcoded dates"
    DAYS_AGO = "DAYS_AGO", "Days ago"


class UserSettings(TimestampModel):
    preferred_currency_id: int | None
    active_trip_id: int | None

    user = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
    )
    preferred_currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    active_trip = models.ForeignKey(
        Trip,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    is_encrypted = models.BooleanField(default=False)
    default_statistics_method = models.CharField(
        max_length=20,
        choices=DefaultStatisticsMethod.choices,
        default=DefaultStatisticsMethod.HARDCODED_DATES,
    )
    default_statistics_start_date = models.DateField(null=True, blank=True)
    default_statistics_end_date = models.DateField(null=True, blank=True)
    # Both count days back from today: a negative number is a day in the future.
    default_statistics_n_days_ago_from = models.IntegerField(
        null=True, blank=True, validators=STATISTICS_DAYS_OFFSET_VALIDATORS
    )
    default_statistics_n_days_ago_to = models.IntegerField(
        null=True, blank=True, validators=STATISTICS_DAYS_OFFSET_VALIDATORS
    )

    @property
    def statistics_start_date(self) -> dt.date:
        """The first day of the period the statistics page opens on."""
        if self._statistics_period_is_relative:
            return _days_ago(
                self.default_statistics_n_days_ago_from,
                DEFAULT_STATISTICS_N_DAYS_AGO_FROM,
            )
        if self.default_statistics_start_date:
            return self.default_statistics_start_date
        return date_utils.today() - relativedelta(months=6)

    @property
    def statistics_end_date(self) -> dt.date:
        """The last day of the period the statistics page opens on."""
        if self._statistics_period_is_relative:
            return _days_ago(
                self.default_statistics_n_days_ago_to,
                DEFAULT_STATISTICS_N_DAYS_AGO_TO,
            )
        return self.default_statistics_end_date or date_utils.today()

    @property
    def _statistics_period_is_relative(self) -> bool:
        return self.default_statistics_method == DefaultStatisticsMethod.DAYS_AGO


def _days_ago(n_days: int | None, default_n_days: int) -> dt.date:
    """The day `n_days` before today, or `default_n_days` before when unspecified."""
    if n_days is None:
        n_days = default_n_days
    return date_utils.today() - dt.timedelta(days=n_days)
