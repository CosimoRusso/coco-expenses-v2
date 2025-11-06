from rest_framework import viewsets, permissions
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework import status
from expenses.serializers.currencies import CurrencySerializer
from expenses.models import Currency


class CurrencyViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CurrencySerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ["code"]
    queryset = Currency.objects.all()

    def create(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
    