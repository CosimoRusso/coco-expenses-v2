from collections import Counter

from expenses.models import Expense, SharedExpense, SharedExpenseParticipant

# How many of the user's latest matching expenses decide the suggestion
HISTORY_SIZE = 3


def suggested_category_id(participant: SharedExpenseParticipant) -> int | None:
    """The category the participant is likely to give to their share, if any.

    It is the active category they gave to most of their latest expenses shared by
    the same creator under the category the creator gave to this one.
    """
    shared_expense = participant.shared_expense
    if participant.user_id == shared_expense.created_by_id:
        return None
    creator_category_id = _creator_category_id(shared_expense)
    if creator_category_id is None:
        return None
    history = _latest_categories(participant, creator_category_id)
    if len(history) < HISTORY_SIZE:
        return None
    (category_id, is_active), occurrences = Counter(history).most_common(1)[0]
    has_majority = occurrences * 2 > HISTORY_SIZE
    return category_id if has_majority and is_active else None


def _creator_category_id(shared_expense: SharedExpense) -> int | None:
    """The category of the expense the creator registered for the shared expense."""
    return (
        Expense.objects.filter(
            user_id=shared_expense.created_by_id,
            shared_expense_participant__shared_expense=shared_expense,
        )
        .values_list("category_id", flat=True)
        .first()
    )


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
