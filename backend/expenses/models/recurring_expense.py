import calendar
import datetime as dt

from django.core.validators import MinValueValidator
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
    amortization_duration = models.IntegerField(
        verbose_name="Amortization Duration",
        null=False,
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Duration for amortization calculation",
    )
    amortization_unit = models.CharField(
        verbose_name="Amortization Unit",
        max_length=10,
        null=False,
        default="DAY",
        choices=[
            ("DAY", "Day"),
            ("WEEK", "Week"),
            ("MONTH", "Month"),
            ("YEAR", "Year"),
        ],
        help_text="Unit of measure for amortization duration",
    )

    def calculate_amortization_dates(
        self, start_date: dt.date
    ) -> tuple[dt.date, dt.date]:
        """
        Calculate amortization start and end dates based on the recurring expense settings.

        Args:
            start_date: The date to start amortization from (typically today)

        Returns:
            Tuple of (amortization_start_date, amortization_end_date)
        """
        amortization_start_date = start_date

        if self.amortization_unit == "DAY":
            amortization_end_date = start_date + dt.timedelta(
                days=self.amortization_duration - 1
            )
        elif self.amortization_unit == "WEEK":
            amortization_end_date = (
                start_date
                + dt.timedelta(weeks=self.amortization_duration)
                - dt.timedelta(days=1)
            )
        elif self.amortization_unit == "MONTH":
            # Calculate end of month: add (duration - 1) months, then get end of that month
            # For duration=1, this means end of current month
            month = start_date.month - 1 + (self.amortization_duration - 1)
            year = start_date.year + month // 12
            month = month % 12 + 1
            # Get the last day of the target month
            last_day = calendar.monthrange(year, month)[1]
            amortization_end_date = dt.date(year, month, last_day)
        elif self.amortization_unit == "YEAR":
            # Calculate end of year: add (duration - 1) years, then get end of that year
            # For duration=1, this means end of current year
            year = start_date.year + (self.amortization_duration - 1)
            amortization_end_date = dt.date(year, 12, 31)
        else:
            # Default to same day if unit is invalid
            amortization_end_date = start_date

        return amortization_start_date, amortization_end_date

    def __str__(self):
        return (
            f"{self.description} - {self.schedule} "
            f"({self.start_date.isoformat()}"
            + (f" -> {self.end_date.isoformat()}" if self.end_date else "")
            + ")"
        )
