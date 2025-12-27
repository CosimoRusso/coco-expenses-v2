import factory
from expenses.models.trip import Trip
from expenses.tests.factories.user_factories import UserFactory


class TripFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Trip

    code = factory.Sequence(lambda n: f"TRIP{n}")
    name = factory.Sequence(lambda n: f"Trip {n}")
    user = factory.SubFactory(UserFactory)
