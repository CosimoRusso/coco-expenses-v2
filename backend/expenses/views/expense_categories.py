from rest_framework import viewsets, permissions

from expenses.models import ExpenseCategory
from expenses.serializers.expense_categories import ExpenseCategorySerializer
from rest_framework.filters import OrderingFilter


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ExpenseCategorySerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ["code"]

    def get_queryset(self):
        user = self.request.user
        return ExpenseCategory.objects.filter(user=user)
