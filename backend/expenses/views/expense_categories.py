from django_filters.rest_framework import DjangoFilterBackend
from expenses.models import ExpenseCategory
from expenses.serializers.expense_categories import ExpenseCategorySerializer
from rest_framework import permissions, viewsets
from rest_framework.filters import OrderingFilter


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ExpenseCategorySerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["is_active"]
    ordering_fields = ["name"]
    ordering = ["name", "id"]

    def get_queryset(self):
        user = self.request.user
        return ExpenseCategory.objects.filter(user=user)
