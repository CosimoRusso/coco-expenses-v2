import factory
from expenses.models import PaymentMethod
from expenses.tests.factories.user_factories import UserFactory


class PaymentMethodFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PaymentMethod

    code = factory.Sequence(lambda n: f"CARD{n}")
    name = factory.Sequence(lambda n: f"Card {n}")
    user = factory.SubFactory(UserFactory)
