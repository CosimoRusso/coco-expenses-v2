from decimal import Decimal

from django.db import models
from expenses.models.currency import Currency
from expenses.models.notification import Notification
from expenses.models.timestamp import TimestampModel
from expenses.models.user import User


class SharedExpenseDeletedNotification(TimestampModel):
    """A shared expense someone deleted, copied because the shared expense is gone."""

    notification: Notification = models.OneToOneField(
        Notification, on_delete=models.PROTECT, related_name="shared_expense_deleted"
    )
    deleted_by: User = models.ForeignKey(User, on_delete=models.PROTECT)
    description: str = models.CharField(max_length=255)
    amount: Decimal = models.DecimalField(max_digits=10, decimal_places=2)
    currency: Currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT, related_name="+"
    )
