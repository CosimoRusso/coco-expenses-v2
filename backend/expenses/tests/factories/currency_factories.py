import factory
from expenses.models.currency import Currency

euro = {
    'code': 'EUR',
    'symbol': '€',
    'display_name': 'Euro',
}
dollar = {
    'code': 'USD',
    'symbol': '$',
    'display_name': 'Dollar',
}
pound = {
    'code': 'GBP',
    'symbol': '£',
    'display_name': 'Pound',
}
currencies = [euro, dollar, pound]

class CurrencyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Currency
        exclude = ['instance']
        django_get_or_create = ['code']

    instance = factory.Iterator(currencies)

    code = factory.LazyAttribute(lambda o: o.instance['code'])
    symbol = factory.LazyAttribute(lambda o: o.instance['symbol'])
    display_name = factory.LazyAttribute(lambda o: o.instance['display_name'])