from django_filters.rest_framework import DjangoFilterBackend
from expenses.models import Trip
from expenses.serializers.trips import TripSerializer
from rest_framework import permissions, viewsets
from rest_framework.filters import OrderingFilter


class TripViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TripSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["is_active"]
    ordering_fields = ["name"]
    ordering = ["name", "id"]

    def get_queryset(self):
        user = self.request.user
        return Trip.objects.filter(user=user)
