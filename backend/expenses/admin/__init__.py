from django.contrib import admin

from expenses.admin.trip import TripAdmin
from expenses.models import User, Trip, Currency, DollarExchangeRate
from expenses.admin.user import UserAdmin
from expenses.admin.currency import CurrencyAdmin
from expenses.admin.dollar_exchange_rate import DollarExchangeRateAdmin

# Register the User model with the custom UserAdmin
admin.site.register(User, UserAdmin)
admin.site.register(Trip, TripAdmin)
admin.site.register(Currency, CurrencyAdmin)
admin.site.register(DollarExchangeRate, DollarExchangeRateAdmin)
