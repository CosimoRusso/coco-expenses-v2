from django.contrib import admin
from django.contrib.admin.exceptions import AlreadyRegistered
from expenses.admin.currency import CurrencyAdmin
from expenses.admin.dollar_exchange_rate import DollarExchangeRateAdmin
from expenses.admin.expense_category import ExpenseCategoryAdmin
from expenses.admin.friend import FriendAdmin
from expenses.admin.notification import NotificationAdmin
from expenses.admin.settings import SettingsAdmin
from expenses.admin.shared_expense import SharedExpenseAdmin
from expenses.admin.shared_expense_deleted_notification import (
    SharedExpenseDeletedNotificationAdmin,
)
from expenses.admin.shared_expense_modified_notification import (
    SharedExpenseModifiedNotificationAdmin,
)
from expenses.admin.shared_expense_notification import SharedExpenseNotificationAdmin
from expenses.admin.shared_expense_participant import SharedExpenseParticipantAdmin
from expenses.admin.trip import TripAdmin
from expenses.admin.user import UserAdmin
from expenses.models import (
    Currency,
    DollarExchangeRate,
    ExpenseCategory,
    Friend,
    Notification,
    Settings,
    SharedExpense,
    SharedExpenseDeletedNotification,
    SharedExpenseModifiedNotification,
    SharedExpenseNotification,
    SharedExpenseParticipant,
    Trip,
    User,
)

# Register the User model with the custom UserAdmin
try:
    admin.site.register(User, UserAdmin)
    admin.site.register(Trip, TripAdmin)
    admin.site.register(Currency, CurrencyAdmin)
    admin.site.register(DollarExchangeRate, DollarExchangeRateAdmin)
    admin.site.register(ExpenseCategory, ExpenseCategoryAdmin)
    admin.site.register(Settings, SettingsAdmin)
    admin.site.register(Friend, FriendAdmin)
    admin.site.register(Notification, NotificationAdmin)
    admin.site.register(SharedExpense, SharedExpenseAdmin)
    admin.site.register(SharedExpenseParticipant, SharedExpenseParticipantAdmin)
    admin.site.register(SharedExpenseNotification, SharedExpenseNotificationAdmin)
    admin.site.register(
        SharedExpenseModifiedNotification, SharedExpenseModifiedNotificationAdmin
    )
    admin.site.register(
        SharedExpenseDeletedNotification, SharedExpenseDeletedNotificationAdmin
    )
except AlreadyRegistered:
    pass
