import factory

from expenses.models import ExpenseCategory
from expenses.tests.factories.user_factories import UserFactory

fake_expense_categories = [
    "home",
    "groceries",
    "mobility",
    "health",
    "rent",
    "shopping",
]

fake_income_categories = ["income", "stocks"]


class CategoryFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = ExpenseCategory


class ExpenseCategoryFactory(CategoryFactory):
    code = factory.Iterator(fake_expense_categories)
    name = factory.Iterator(fake_expense_categories)
    for_expense = True


class IncomeCategoryFactory(CategoryFactory):
    code = factory.Iterator(fake_income_categories)
    name = factory.Iterator(fake_income_categories)
    for_expense = False
