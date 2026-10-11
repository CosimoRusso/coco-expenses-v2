from typing import TYPE_CHECKING

from django.db import models

from expenses.models.shared_expense import SharedExpense
from expenses.models.timestamp import TimestampModel
from expenses.models.user import User

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from expenses.models.expense import Expense


class SharedExpenseParticipant(TimestampModel):
    user_id: int
    expense_set: "RelatedManager[Expense]"

    user = models.ForeignKey(User, on_delete=models.PROTECT, null=False, blank=False)
    shared_expense = models.ForeignKey(
        SharedExpense, on_delete=models.PROTECT, null=False, blank=False
    )
    quota = models.DecimalField(
        null=False, blank=False, max_digits=10, decimal_places=2
    )
    # What the shared expense was called when the user registered their expense;
    # empty until then.
    description_when_registered = models.CharField(
        blank=True, default="", max_length=255
    )
