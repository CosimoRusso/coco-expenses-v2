from django.db import models
from expenses.models.notification import Notification
from expenses.models.shared_expense_participant import SharedExpenseParticipant
from expenses.models.timestamp import TimestampModel


class SharedExpenseNotification(TimestampModel):
    notification: Notification = models.ForeignKey(
        Notification, on_delete=models.PROTECT, null=False, blank=False
    )
    shared_expense_participant = models.ForeignKey(
        SharedExpenseParticipant, on_delete=models.PROTECT, null=False, blank=False
    )
