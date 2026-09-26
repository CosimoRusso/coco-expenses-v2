from expenses.balances import balances_of, movement_of, shared_expenses_with
from expenses.models import Currency, UserSettings
from expenses.serializers.balances import BalancesSerializer, MovementSerializer
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class BalanceViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    lookup_value_regex = r"\d+"

    def list(self, request):
        """The user's balance with each person, in their favourite currency."""
        user_settings = UserSettings.objects.get_or_create(user=request.user)[0]
        currency = user_settings.preferred_currency or Currency.objects.get(code="USD")
        data = {"currency": currency, "balances": balances_of(request.user, currency)}
        return Response(BalancesSerializer(data).data)

    @action(detail=True)
    def movements(self, request, pk=None):
        """Every shared expense between the user and the person `pk`, paginated."""
        paginator = PageNumberPagination()
        participants = paginator.paginate_queryset(
            shared_expenses_with(request.user, other_id=int(pk)), request, view=self
        )
        movements = [movement_of(p, request.user) for p in participants]
        serializer = MovementSerializer(movements, many=True)
        return paginator.get_paginated_response(serializer.data)
