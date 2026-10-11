from django.db import models

from expenses.models.currency import Currency
from expenses.models.notification import Notification
from expenses.models.shared_expense import SharedExpense
from expenses.models.timestamp import TimestampModel
from expenses.models.user import User


class SharedExpenseModifiedNotification(TimestampModel):
    """What changed in a shared expense, as seen by the participant notified."""

    notification = models.OneToOneField(
        Notification, on_delete=models.PROTECT, related_name="shared_expense_modified"
    )
    shared_expense = models.ForeignKey(SharedExpense, on_delete=models.PROTECT)
    modified_by = models.ForeignKey(User, on_delete=models.PROTECT)
    amount_before = models.DecimalField(max_digits=10, decimal_places=2)
    currency_before = models.ForeignKey(
        Currency, on_delete=models.PROTECT, related_name="+"
    )
    amount_after = models.DecimalField(max_digits=10, decimal_places=2)
    currency_after = models.ForeignKey(
        Currency, on_delete=models.PROTECT, related_name="+"
    )
    number_participants_before = models.PositiveIntegerField()
    number_participants_after = models.PositiveIntegerField()
    you_were_added = models.BooleanField(default=False)
    you_were_removed = models.BooleanField(default=False)
