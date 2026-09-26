from expenses.balances import balances_of
from expenses.models import Currency, UserSettings
from expenses.serializers.balances import BalancesSerializer
from rest_framework import permissions, viewsets
from rest_framework.response import Response


class BalanceViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """The user's balance with each person, in their favourite currency."""
        user_settings = UserSettings.objects.get_or_create(user=request.user)[0]
        currency = user_settings.preferred_currency or Currency.objects.get(code="USD")
        data = {"currency": currency, "balances": balances_of(request.user, currency)}
        return Response(BalancesSerializer(data).data)
