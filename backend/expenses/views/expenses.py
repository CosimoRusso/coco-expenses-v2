from rest_framework import permissions, viewsets

from expenses.models import Expense
from expenses.serializers.expenses import ExpenseSerializer


class ExpenseViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        user = self.request.user
        return Expense.objects.select_related("category", "trip").filter(user=user)
