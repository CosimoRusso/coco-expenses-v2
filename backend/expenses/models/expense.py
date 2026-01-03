from django.db import models


class Expense(models.Model):
    user = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="expenses",
    )
    expense_date = models.DateField(verbose_name="Expense Date", null=True)
    description = models.CharField(verbose_name="Description", max_length=255)
    amount = models.DecimalField(
        verbose_name="Actual Amount", decimal_places=2, max_digits=10, null=True
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
    # True for expenses, false for income
    is_expense = models.BooleanField(default=True)
    currency = models.ForeignKey(
        "Currency", on_delete=models.PROTECT, related_name="expenses", null=True
    )
    recurring_expense = models.ForeignKey(
        "RecurringExpense", on_delete=models.PROTECT, related_name="expenses", null=True
    )

    def __str__(self):
        return (
            f"{self.description} - {self.amount} "
            f"({self.amortization_start_date.isoformat()} -> {self.amortization_end_date.isoformat()})"
        )
