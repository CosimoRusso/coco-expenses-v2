from django.contrib import admin
from django.contrib.admin.exceptions import AlreadyRegistered
from expenses.admin.currency import CurrencyAdmin
from expenses.admin.dollar_exchange_rate import DollarExchangeRateAdmin
from expenses.admin.settings import SettingsAdmin
from expenses.admin.trip import TripAdmin
from expenses.admin.user import UserAdmin
from expenses.models import Currency, DollarExchangeRate, Settings, Trip, User

# Register the User model with the custom UserAdmin
try:
    admin.site.register(User, UserAdmin)
    admin.site.register(Trip, TripAdmin)
    admin.site.register(Currency, CurrencyAdmin)
    admin.site.register(DollarExchangeRate, DollarExchangeRateAdmin)
    admin.site.register(Settings, SettingsAdmin)
except AlreadyRegistered:
    pass
