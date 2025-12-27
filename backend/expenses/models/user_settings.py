from django.db import models


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
