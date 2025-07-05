from rest_framework import viewsets, permissions

from expenses.models import Trip
from expenses.serializers.trips import TripSerializer


class TripViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TripSerializer

    def get_queryset(self):
        user = self.request.user
        return Trip.objects.filter(user=user)
