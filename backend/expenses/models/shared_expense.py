from decimal import Decimal

from django.db import models
from expenses.models.currency import Currency
from expenses.models.timestamp import TimestampModel
from expenses.models.user import User


class SharedExpense(TimestampModel):
    description: str = models.CharField(null=False, blank=False, max_length=255)
    amount: Decimal = models.DecimalField(
        null=False, blank=False, max_digits=10, decimal_places=2
    )
    currency: Currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT, null=False, blank=False
    )
    created_by: User = models.ForeignKey(
        User, on_delete=models.PROTECT, null=False, blank=False
    )
