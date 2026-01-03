import factory
from expenses import date_utils
from expenses.models import RecurringExpense
from expenses.tests.factories.category_factories import ExpenseCategoryFactory
from expenses.tests.factories.currency_factories import CurrencyFactory
from expenses.tests.factories.user_factories import UserFactory
from factory.fuzzy import FuzzyDecimal, FuzzyText


class RecurringExpenseFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    start_date = factory.LazyAttribute(lambda o: date_utils.today())
    end_date = None
    amount = FuzzyDecimal(10, 1000, precision=2)
    category = factory.SubFactory(ExpenseCategoryFactory)
    trip = None
    schedule = factory.LazyAttribute(
        lambda o: "0 0 * * *"
    )  # Daily at midnight (crontab syntax)
    description = FuzzyText(length=20)
    is_expense = True
    currency = factory.SubFactory(CurrencyFactory)

    class Meta:
        model = RecurringExpense
