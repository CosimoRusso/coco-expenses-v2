from expenses.models import UserSettings
from expenses.tests.factories.user_factories import UserFactory
import factory
from expenses.tests.factories.currency_factories import CurrencyFactory
from expenses.tests.factories.trip_factories import TripFactory


class UserSettingsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserSettings

    user = factory.SubFactory(UserFactory)
    preferred_currency = factory.SubFactory(CurrencyFactory)
    active_trip = factory.SubFactory(TripFactory)