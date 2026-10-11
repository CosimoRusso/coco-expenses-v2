from django.db import models

from expenses.models.currency import Currency
from expenses.models.notification import Notification
from expenses.models.timestamp import TimestampModel
from expenses.models.user import User


class SharedExpenseDeletedNotification(TimestampModel):
    """A shared expense someone deleted, copied because the shared expense is gone."""

    notification = models.OneToOneField(
        Notification, on_delete=models.PROTECT, related_name="shared_expense_deleted"
    )
    deleted_by = models.ForeignKey(User, on_delete=models.PROTECT)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="+")
