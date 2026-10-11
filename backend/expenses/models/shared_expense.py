from typing import TYPE_CHECKING

from django.db import models

from expenses.models.currency import Currency
from expenses.models.timestamp import TimestampModel
from expenses.models.user import User

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from expenses.models.shared_expense_participant import SharedExpenseParticipant


class SharedExpense(TimestampModel):
    created_by_id: int
    sharedexpenseparticipant_set: "RelatedManager[SharedExpenseParticipant]"

    description = models.CharField(null=False, blank=False, max_length=255)
    amount = models.DecimalField(
        null=False, blank=False, max_digits=10, decimal_places=2
    )
    currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT, null=False, blank=False
    )
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, null=False, blank=False
    )
