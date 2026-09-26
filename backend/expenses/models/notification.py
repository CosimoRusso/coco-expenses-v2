from django.db import models
from expenses.models.timestamp import TimestampModel
from expenses.models.user import User


class NotificationKind(models.TextChoices):
    FRIEND_REQUEST_RECEIVED = "FRIEND_REQUEST_RECEIVED", "Friend request received"
    FRIEND_REQUEST_ACCEPTED = "FRIEND_REQUEST_ACCEPTED", "Friend request accepted"
    FRIEND_REQUEST_REJECTED = "FRIEND_REQUEST_REJECTED", "Friend request rejected"
    SHARED_EXPENSE_REQUESTED = "SHARED_EXPENSE_REQUESTED", "Shared expense requested"
    SHARED_EXPENSE_ACCEPTED = "SHARED_EXPENSE_ACCEPTED", "Shared expense accepted"
    SHARED_EXPENSE_REJECTED = "SHARED_EXPENSE_REJECTED", "Shared expense rejected"
    SHARED_EXPENSE_MODIFIED = "SHARED_EXPENSE_MODIFIED", "Shared expense modified"
    SHARED_EXPENSE_DELETED = "SHARED_EXPENSE_DELETED", "Shared expense deleted"


class Notification(TimestampModel):
    user: User = models.ForeignKey(
        User, on_delete=models.PROTECT, null=False, blank=False
    )
    kind = models.CharField(max_length=50, choices=NotificationKind.choices)
    read_at = models.DateTimeField(null=True, blank=True)
