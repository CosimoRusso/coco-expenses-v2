from expenses.models.dollar_exchange_rate import DollarExchangeRate
import factory


class DollarExchangeRateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DollarExchangeRate