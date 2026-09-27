from django.db.models import ProtectedError
from django_filters.rest_framework import DjangoFilterBackend
from expenses.models import PaymentMethod
from expenses.serializers.payment_methods import PaymentMethodSerializer
from rest_framework import permissions, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter


class PaymentMethodViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentMethodSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["is_active"]
    ordering_fields = ["name", "code"]
    ordering = ["name", "id"]

    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user)

    def perform_destroy(self, instance: PaymentMethod):
        """A payment method used by some expense cannot be deleted."""
        try:
            instance.delete()
        except ProtectedError as error:
            raise ValidationError(
                {
                    "detail": "This payment method is used by some expenses, "
                    "deactivate it instead"
                }
            ) from error
