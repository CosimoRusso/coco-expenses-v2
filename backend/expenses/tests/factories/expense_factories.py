import factory
from factory.fuzzy import FuzzyText, FuzzyDecimal

from expenses import date_utils
from expenses.models import Expense
from expenses.tests.factories.user_factories import UserFactory
from expenses.tests.factories.category_factories import ExpenseCategoryFactory


class ExpenseFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    expense_date = factory.LazyAttribute(lambda o: date_utils.today())
    description = FuzzyText(length=20)
    forecast_amount = FuzzyDecimal(10, 1000, precision=2)
    actual_amount = FuzzyDecimal(10, 1000, precision=2)
    amortization_start_date = factory.LazyAttribute(lambda o: date_utils.today())
    amortization_end_date = factory.LazyAttribute(lambda o: date_utils.today())
    category = factory.SubFactory(ExpenseCategoryFactory)
    trip = None
    is_expense = True

    class Meta:
        model = Expense
