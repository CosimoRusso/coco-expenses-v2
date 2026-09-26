from decimal import Decimal

from django.db import models
from expenses.models.currency import Currency
from expenses.models.notification import Notification
from expenses.models.shared_expense import SharedExpense
from expenses.models.timestamp import TimestampModel
from expenses.models.user import User


class SharedExpenseModifiedNotification(TimestampModel):
    """What changed in a shared expense, as seen by the participant notified."""

    notification: Notification = models.OneToOneField(
        Notification, on_delete=models.PROTECT, related_name="shared_expense_modified"
    )
    shared_expense: SharedExpense = models.ForeignKey(
        SharedExpense, on_delete=models.PROTECT
    )
    modified_by: User = models.ForeignKey(User, on_delete=models.PROTECT)
    amount_before: Decimal = models.DecimalField(max_digits=10, decimal_places=2)
    currency_before: Currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT, related_name="+"
    )
    amount_after: Decimal = models.DecimalField(max_digits=10, decimal_places=2)
    currency_after: Currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT, related_name="+"
    )
    number_participants_before: int = models.PositiveIntegerField()
    number_participants_after: int = models.PositiveIntegerField()
    you_were_added: bool = models.BooleanField(default=False)
    you_were_removed: bool = models.BooleanField(default=False)
