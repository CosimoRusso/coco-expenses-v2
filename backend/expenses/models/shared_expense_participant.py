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
