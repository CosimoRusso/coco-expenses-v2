from rest_framework import permissions, viewsets

from expenses.models import Expense


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all().order_by("expense_date")
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Expense.objects.select_related("category", "trip").filter(user=user)
