from django.db import models


class ExpenseCategory(models.Model):
    user = models.ForeignKey(
        "User", on_delete=models.PROTECT, related_name="expense_categories"
    )
    code = models.CharField(verbose_name="Expense Category", max_length=128)
    name = models.CharField(verbose_name="Expense Category", max_length=128)

    class Meta:
        unique_together = ("user", "code")
