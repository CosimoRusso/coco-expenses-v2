from dataclasses import dataclass
import datetime as dt
from collections import defaultdict
from decimal import Decimal
from typing import Iterable

from expenses.managers import exchange_rate_manager
from expenses.models import Expense
from expenses.models.currency import Currency
from expenses.models.expense_category import ExpenseCategory
from expenses.models.trip import Trip
ZERO = Decimal("0.00")

@dataclass
class StatisticsExpense:
    amount: Decimal
    currency: Currency
    expense_date: dt.date
    amortization_start_date: dt.date
    amortization_end_date: dt.date
    category: ExpenseCategory
    trip: Trip
    is_expense: bool

def get_expenses_by_day(expenses: list[StatisticsExpense]) -> dict[dt.date, list[StatisticsExpense]]:
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
                ammortized_row = StatisticsExpense(
                    expense_date=expense.expense_date,
                    amount=amortize_value(expense.amount, num_days),
                    currency=expense.currency,
                    amortization_start_date=current_day,
                    amortization_end_date=current_day,
                    category=expense.category, 
                    trip=expense.trip, 
                    is_expense=expense.is_expense
                )
                expenses_by_day[current_day].append(ammortized_row)
    return expenses_by_day


def amortize_value(value: Decimal | None, num_days: int) -> Decimal:
    """Distributes a value evenly across a number of days."""
    if not value:
        return ZERO
    return (value / num_days).quantize(ZERO)

def convert_expenses_to_statistics_expenses(expenses: Iterable[Expense]) -> list[StatisticsExpense]:
    res = []
    for expense in expenses:
        res.append(StatisticsExpense(
            amount=expense.amount, 
            currency=expense.currency, 
            expense_date=expense.expense_date, 
            amortization_start_date=expense.amortization_start_date, 
            amortization_end_date=expense.amortization_end_date, 
            category=expense.category, 
            trip=expense.trip,
            is_expense=expense.is_expense
        ))
    return res

def convert_expenses_to_currency(expenses: list[StatisticsExpense], currency: Currency) -> list[StatisticsExpense]:
    expenses_as_money = [exchange_rate_manager.Money(amount=expense.amount, currency=expense.currency, day=expense.expense_date) for expense in expenses]
    money_in_currency = exchange_rate_manager.bulk_convert_to_currency(expenses_as_money, currency)
    return [StatisticsExpense(
        amount=money.amount, 
        currency=currency, 
        expense_date=money.day, 
        amortization_start_date=expense.amortization_start_date, 
        amortization_end_date=expense.amortization_end_date, 
        category=expense.category, 
        trip=expense.trip, 
        is_expense=expense.is_expense
    )
    for money, expense in zip(money_in_currency, expenses)
    ]

def get_expenses_date_range_in_currency(
    expenses: Iterable[Expense], start_date: dt.date, end_date: dt.date, currency: Currency
) -> dict[dt.date, list[StatisticsExpense]]:
    expenses_as_statistics_expenses = convert_expenses_to_statistics_expenses(expenses)
    expenses_in_currency = convert_expenses_to_currency(expenses_as_statistics_expenses, currency)

    expenses_by_day = get_expenses_by_day(expenses_in_currency)
    return {
        day: [expense for expense in expenses_by_day[day]]
        for day in expenses_by_day
        if start_date <= day <= end_date
    }


def get_non_expenses_date_range(
    expenses: Iterable[Expense], start_date: dt.date, end_date: dt.date
) -> dict[dt.date, list[Expense]]:
    expenses_by_day = get_expenses_by_day(expenses)
    return {
        day: [expense for expense in expenses_by_day[day] if not expense.is_expense]
        for day in expenses_by_day
        if start_date <= day <= end_date
    }
