from django.db import models


class RecurringExpense(models.Model):
    user = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="recurring_expenses",
    )
    start_date = models.DateField(verbose_name="Start Date", null=False)
    end_date = models.DateField(verbose_name="End Date", null=True, blank=True)
    category = models.ForeignKey(
        "ExpenseCategory",
        on_delete=models.PROTECT,
        related_name="recurring_expenses",
        null=False,
    )
    trip = models.ForeignKey(
        "Trip",
        on_delete=models.PROTECT,
        related_name="recurring_expenses",
        null=True,
        blank=True,
    )
    schedule = models.CharField(
        verbose_name="Schedule",
        max_length=255,
        null=False,
        help_text="Schedule in crontab syntax",
    )
    description = models.CharField(
        verbose_name="Description",
        max_length=255,
        null=False,
    )
    # True for expenses, false for income
    is_expense = models.BooleanField(
        verbose_name="Is Expense",
        null=False,
        default=True,
    )
    currency = models.CharField(
        verbose_name="Currency",
        max_length=10,
        null=False,
    )

    def __str__(self):
        return (
            f"{self.description} - {self.schedule} "
            f"({self.start_date.isoformat()}"
            + (f" -> {self.end_date.isoformat()}" if self.end_date else "")
            + ")"
        )
