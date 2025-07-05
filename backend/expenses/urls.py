from rest_framework import routers

from expenses.views.expense_categories import ExpenseCategoryViewSet
from expenses.views.expenses import ExpenseViewSet
from expenses.views.trips import TripViewSet
from expenses.views.users import UserViewSet

app_name = "expenses"

router = routers.DefaultRouter()
router.register("expenses", ExpenseViewSet, basename="expenses")
router.register(
    "expense-categories", ExpenseCategoryViewSet, basename="expense-categories"
)
router.register("trips", TripViewSet, basename="trips")
router.register("users", UserViewSet, basename="users")

urlpatterns = router.urls
