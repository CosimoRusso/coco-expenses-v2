import datetime as dt
from collections import Counter
from dataclasses import dataclass

from expenses.models import Expense, SharedExpenseParticipant

# How many of the user's latest matching expenses decide the suggested category
HISTORY_SIZE = 3


@dataclass(frozen=True)
class ShareSuggestion:
    """Values to prefill in the expense a participant registers for their share."""

    category: int | None = None
    expense_date: dt.date | None = None
    amortization_start_date: dt.date | None = None
    amortization_end_date: dt.date | None = None


def suggestion_for(participant: SharedExpenseParticipant) -> ShareSuggestion:
    """The creator's dates, and the category the participant is likely to pick.

    Nothing is suggested to the creator, or while the creator has no expense for it.
    """
    creator_expense = _creator_expense(participant)
    if creator_expense is None or creator_expense.user_id == participant.user_id:
        return ShareSuggestion()
    return ShareSuggestion(
        category=_suggested_category_id(participant, creator_expense.category_id),
        expense_date=creator_expense.expense_date,
        amortization_start_date=creator_expense.amortization_start_date,
        amortization_end_date=creator_expense.amortization_end_date,
    )


def _creator_expense(participant: SharedExpenseParticipant) -> Expense | None:
    """The expense the creator registered for the participant's shared expense."""
    shared_expense = participant.shared_expense
    return Expense.objects.filter(
        user_id=shared_expense.created_by_id,
        shared_expense_participant__shared_expense=shared_expense,
    ).first()


def _suggested_category_id(
    participant: SharedExpenseParticipant, creator_category_id: int
) -> int | None:
    """The active category the participant gave to most of their latest expenses shared
    by the same creator under `creator_category_id`."""
    history = _latest_categories(participant, creator_category_id)
    if len(history) < HISTORY_SIZE:
        return None
    (category_id, is_active), occurrences = Counter(history).most_common(1)[0]
    has_majority = occurrences * 2 > HISTORY_SIZE
    return category_id if has_majority and is_active else None


def _latest_categories(
    participant: SharedExpenseParticipant, creator_category_id: int
) -> list[tuple[int, bool]]:
    """Category and whether it is active, for each of the participant's latest expenses
    shared by the same creator under `creator_category_id`."""
    creator_id = participant.shared_expense.created_by_id
    shared_expenses_in_category = Expense.objects.filter(
        user_id=creator_id,
        category_id=creator_category_id,
        shared_expense_participant__shared_expense__created_by_id=creator_id,
    ).values("shared_expense_participant__shared_expense_id")
    expenses = Expense.objects.filter(
        user_id=participant.user_id,
        shared_expense_participant__shared_expense__in=shared_expenses_in_category,
    ).order_by("-id")
    return list(
        expenses.values_list("category_id", "category__is_active")[:HISTORY_SIZE]
    )
