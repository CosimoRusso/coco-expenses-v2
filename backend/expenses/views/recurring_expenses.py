from rest_framework import permissions, viewsets
from rest_framework.filters import OrderingFilter
import django_filters
from django_filters.rest_framework import DjangoFilterBackend

from expenses.models import RecurringExpense
from expenses.serializers.recurring_expenses import RecurringExpenseSerializer


class RecurringExpenseFilterSet(django_filters.FilterSet):
    is_expense = django_filters.BooleanFilter()
    category = django_filters.NumberFilter()
    trip = django_filters.NumberFilter()

    class Meta:
        model = RecurringExpense
        fields = ["is_expense", "category", "trip"]


class RecurringExpenseViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RecurringExpenseSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = RecurringExpenseFilterSet
    ordering_fields = [
        "start_date",
        "end_date",
    ]
    ordering = ["-start_date"]

    def get_queryset(self):
        user = self.request.user
        return (
            RecurringExpense.objects.select_related("category", "trip")
            .filter(user=user)
            .order_by("-start_date")
        )

