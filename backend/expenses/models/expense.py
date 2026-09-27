from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from expenses.models.shared_expense_participant import SharedExpenseParticipant


class Expense(models.Model):
    user = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="expenses",
    )
    expense_date = models.DateField(verbose_name="Expense Date", null=True)
    description = models.CharField(verbose_name="Description", max_length=255)
    encrypted_description = models.CharField(
        verbose_name="Encrypted Description", max_length=255, blank=True
    )
    amount = models.DecimalField(
        verbose_name="Actual Amount", decimal_places=2, max_digits=10, null=True
    )
    encrypted_amount = models.CharField(
        verbose_name="Encrypted Amount", max_length=255, blank=True
    )
    amortization_start_date = models.DateField(
        verbose_name="Amortization Start Date", null=True
    )
    amortization_end_date = models.DateField(
        verbose_name="Amortization End Date", null=True
    )
    category = models.ForeignKey(
        "ExpenseCategory", on_delete=models.PROTECT, related_name="expenses"
    )
    trip = models.ForeignKey(
        "Trip", on_delete=models.PROTECT, related_name="expenses", null=True
    )
    payment_method = models.ForeignKey(
        "PaymentMethod",
        on_delete=models.PROTECT,
        related_name="expenses",
        null=True,
        blank=True,
    )
    # True for expenses, false for income
    is_expense = models.BooleanField(default=True)
    currency = models.ForeignKey(
        "Currency", on_delete=models.PROTECT, related_name="expenses", null=True
    )
    recurring_expense = models.ForeignKey(
        "RecurringExpense", on_delete=models.PROTECT, related_name="expenses", null=True
    )
    shared_expense_participant: "SharedExpenseParticipant" = models.ForeignKey(
        "SharedExpenseParticipant", on_delete=models.PROTECT, null=True, blank=True
    )

    def __str__(self):
        is_shared = self.shared_expense_participant is not None
        out = (
            f"{self.description} - {self.amount} "
            f"({self.amortization_start_date.isoformat()} -> {self.amortization_end_date.isoformat()})"
        )
        if is_shared:
            out += ", shared"
        return out

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["shared_expense_participant"],
                name="unique_expense_per_shared_expense_participant",
            )
        ]
