from expenses.views.currencies import CurrencyViewSet
from expenses.views.expense_categories import ExpenseCategoryViewSet
from expenses.views.expenses import ExpenseViewSet
from expenses.views.friends import FriendViewSet
from expenses.views.notifications import NotificationViewSet
from expenses.views.recurring_expenses import RecurringExpenseViewSet
from expenses.views.statistics import StatisticViewSet
from expenses.views.trips import TripViewSet
from expenses.views.user_settings import UserSettingsViewSet
from expenses.views.users import UserViewSet
from rest_framework import routers

app_name = "expenses"

router = routers.DefaultRouter()
router.register("expenses", ExpenseViewSet, basename="expenses")
router.register(
    "expense-categories", ExpenseCategoryViewSet, basename="expense-categories"
)
router.register(
    "recurring-expenses", RecurringExpenseViewSet, basename="recurring-expenses"
)
router.register("trips", TripViewSet, basename="trips")
router.register("users", UserViewSet, basename="users")
router.register("user-settings", UserSettingsViewSet, basename="user-settings")
router.register("statistics", StatisticViewSet, basename="statistics")
router.register("currencies", CurrencyViewSet, basename="currencies")
router.register("friends", FriendViewSet, basename="friends")
router.register("notifications", NotificationViewSet, basename="notifications")

urlpatterns = router.urls
