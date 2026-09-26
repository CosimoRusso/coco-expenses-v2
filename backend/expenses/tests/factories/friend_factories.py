import factory
from expenses.models.friend import Friend
from expenses.tests.factories.user_factories import UserFactory


class FriendFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Friend

    user_1 = factory.SubFactory(UserFactory)
    user_2 = factory.SubFactory(UserFactory)
