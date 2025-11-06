from django.contrib import admin

from expenses.admin.trip import TripAdmin
from expenses.models import User, Trip, Currency
from expenses.admin.user import UserAdmin
from expenses.admin.currency import CurrencyAdmin

# Register the User model with the custom UserAdmin
admin.site.register(User, UserAdmin)
admin.site.register(Trip, TripAdmin)
admin.site.register(Currency, CurrencyAdmin)
