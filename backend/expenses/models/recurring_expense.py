import datetime as dt

from django.db import models
from django.db.models import Exists, OuterRef, Q, Subquery
from expenses import date_utils
from expenses.models import Expense


class RecurringExpenseQuerySet(models.QuerySet):
    def annotate_is_active(self):
        today = date_utils.today()
        return self.annotate(
            is_active=Q(
                Q(start_date__lte=today)
                & (Q(end_date__gte=today) | Q(end_date__isnull=True))
            )
        )

    def annotate_has_expense_in_day(self, day: dt.date):
        return self.annotate(
            has_expense_in_day=Exists(
                Subquery(
                    Expense.objects.filter(
                        recurring_expense=OuterRef("pk"), expense_date=day
                    )
                )
            )
        )


class RecurringExpenseManager(models.Manager):
    pass


class RecurringExpense(models.Model):
    objects = RecurringExpenseManager.from_queryset(RecurringExpenseQuerySet)()

    user = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="recurring_expenses",
    )
    start_date = models.DateField(verbose_name="Start Date", null=False)
    end_date = models.DateField(verbose_name="End Date", null=True, blank=True)
    amount = models.DecimalField(
        verbose_name="Amount",
        max_digits=10,
        decimal_places=2,
        null=False,
    )
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
    currency = models.ForeignKey(
        "Currency",
        on_delete=models.PROTECT,
        related_name="reurring_expenses",
        verbose_name="Currency",
        null=False,
    )

    def __str__(self):
        return (
            f"{self.description} - {self.schedule} "
            f"({self.start_date.isoformat()}"
            + (f" -> {self.end_date.isoformat()}" if self.end_date else "")
            + ")"
        )
