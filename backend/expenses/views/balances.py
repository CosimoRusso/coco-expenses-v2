from typing import cast

from expenses.balances import balances_of, movement_of, shared_expenses_with
from expenses.models import Currency, SharedExpenseParticipant, UserSettings
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
    def movements(self, request, pk: str):
        """Every shared expense between the user and the person `pk`, paginated."""
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(
            shared_expenses_with(request.user, other_id=int(pk)), request, view=self
        )
        # The stubs type the page as `list[Page] | None`: it holds the rows, and is
        # None only when no page size is configured.
        participants = cast("list[SharedExpenseParticipant]", page)
        movements = [movement_of(p, request.user) for p in participants]
        serializer = MovementSerializer(movements, many=True)
        return paginator.get_paginated_response(serializer.data)
