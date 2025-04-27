import factory

from expenses import date_utils
from expenses.models import User
from expenses.models.user import get_hashed_password
import datetime as dt

last_year = dt.date(date_utils.year() - 1, 1, 1)


class UserFactory(factory.django.DjangoModelFactory):
    index = factory.Sequence(lambda n: n + 1)

    first_name = factory.lazy_attribute(lambda u: f"name{u.index}")
    last_name = factory.lazy_attribute(lambda u: f"surname{u.index}")
    email = factory.LazyAttribute(lambda u: f"user{u.index}@test.com")
    email_confirmed_at = factory.LazyAttribute(lambda u: last_year)
    password_hash = factory.LazyAttribute(lambda u: get_hashed_password("password"))

    class Meta:
        model = User
        exclude = ("index",)
