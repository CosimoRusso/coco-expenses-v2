from decimal import Decimal

from django.db import models
from expenses.models.shared_expense import SharedExpense
from expenses.models.timestamp import TimestampModel
from expenses.models.user import User


class SharedExpenseParticipant(TimestampModel):
    user: User = models.ForeignKey(
        User, on_delete=models.PROTECT, null=False, blank=False
    )
    shared_expense: SharedExpense = models.ForeignKey(
        SharedExpense, on_delete=models.PROTECT, null=False, blank=False
    )
    quota: Decimal = models.DecimalField(
        null=False, blank=False, max_digits=10, decimal_places=2
    )
    # What the shared expense was called when the user registered their expense;
    # empty until then.
    description_when_registered: str = models.CharField(
        blank=True, default="", max_length=255
    )
