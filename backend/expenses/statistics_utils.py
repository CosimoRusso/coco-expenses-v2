import datetime as dt
from collections import defaultdict
from decimal import Decimal
from typing import Iterable

from expenses.models import Expense

ZERO = Decimal("0.00")


def get_expenses_by_day(expenses: Iterable[Expense]) -> dict[dt.date, list[Expense]]:
    """Distributes expenses across days based on amortization dates."""
    expenses_by_day = defaultdict(list)
    for expense in expenses:
        if expense.amortization_start_date == expense.amortization_end_date:
            expenses_by_day[expense.amortization_start_date].append(expense)
        else:
            num_days = (
                expense.amortization_end_date - expense.amortization_start_date
            ).days + 1
            for day in range(
                (expense.amortization_end_date - expense.amortization_start_date).days
                + 1
            ):
                current_day = expense.amortization_start_date + dt.timedelta(days=day)
                ammortized_row = Expense(
                    expense_date=expense.expense_date,
                    description=expense.description,
                    actual_amount=Decimal(expense.actual_amount / num_days).quantize(
                        ZERO
                    ),
                    forecast_amount=Decimal(
                        expense.forecast_amount / num_days
                    ).quantize(ZERO),
                    amortization_start_date=current_day,
                    amortization_end_date=current_day,
                    category=expense.category,
                    trip=expense.trip,
                    is_expense=expense.is_expense,
                )
                expenses_by_day[current_day].append(ammortized_row)
    return expenses_by_day


def get_expenses_date_range(
    expenses: Iterable[Expense], start_date: dt.date, end_date: dt.date
) -> dict[dt.date, list[Expense]]:
    expenses_by_day = get_expenses_by_day(expenses)
    return {
        day: expenses_by_day[day]
        for day in expenses_by_day
        if start_date <= day <= end_date
    }
