from rest_framework import routers

from expenses.views.expense_categories import ExpenseCategoryViewSet
from expenses.views.expenses import ExpenseViewSet
from expenses.views.statistics import StatisticViewSet
from expenses.views.trips import TripViewSet
from expenses.views.users import UserViewSet
from expenses.views.currencies import CurrencyViewSet
from expenses.views.user_settings import UserSettingsViewSet

app_name = "expenses"

router = routers.DefaultRouter()
router.register("expenses", ExpenseViewSet, basename="expenses")
router.register(
    "expense-categories", ExpenseCategoryViewSet, basename="expense-categories"
)
router.register("trips", TripViewSet, basename="trips")
router.register("users", UserViewSet, basename="users")
router.register("user-settings", UserSettingsViewSet, basename="user-settings")
router.register("statistics", StatisticViewSet, basename="statistics")
router.register("currencies", CurrencyViewSet, basename="currencies")

urlpatterns = router.urls
