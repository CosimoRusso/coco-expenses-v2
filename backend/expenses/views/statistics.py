from expenses.favourite_currency_cache import (
    MissingCryptoKey,
    favourite_currency,
    populate_favourite_currency_amounts,
)
from expenses.models import ExpenseCategory, Trip
from expenses.serializers.statistics import (
    AmortizationTimelineSerializer,
    CategoryStatisticsSerializer,
    StatisticsInputSerializer,
    TripStatisticsSerializer,
)
from expenses.serializers.trips import TripSerializer
from expenses.statistics_utils import (
    ZERO,
    DatabaseStatistics,
    DecryptedStatistics,
    Period,
    TripTotals,
    statistics_for,
)
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

NO_TRIP = {"id": None, "code": "", "name": "No Trip", "is_active": False}


class StatisticViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["GET"])
    def expense_categories(self, request, *args, **kwargs):
        period = _period(request)
        amounts = _up_to_date_statistics(request).category_amounts(period)
        currency = favourite_currency(request.user)
        categories = ExpenseCategory.objects.filter(user=request.user, for_expense=True)
        result = [
            {
                "category": category,
                "currency": currency,
                "amount": amounts.get(category.id, ZERO),
            }
            for category in categories
        ]
        serializer = CategoryStatisticsSerializer(result, many=True)
        return Response(
            sorted(
                serializer.data, key=lambda item: float(item["amount"]), reverse=True
            )
        )

    @action(detail=False, methods=["GET"])
    def trips(self, request, *args, **kwargs):
        period = _period(request)
        totals = _up_to_date_statistics(request).trip_totals(period)
        currency = favourite_currency(request.user)
        trips = Trip.objects.filter(user=request.user).order_by("name")
        result = [
            {**TripSerializer(trip).data, **_trip_statistics(totals.get(trip.id))}
            for trip in trips
        ]
        result.append({**NO_TRIP, **_trip_statistics(totals.get(None))})
        serializer = TripStatisticsSerializer(
            [{**trip, "currency": currency} for trip in result], many=True
        )
        return Response(
            sorted(
                serializer.data,
                key=lambda item: float(item["total_amount"]),
                reverse=True,
            )
        )

    @action(detail=False, methods=["GET"])
    def amortization_timeline(self, request, *args, **kwargs):
        period = _period(request)
        timeline = _up_to_date_statistics(request).timeline(period)
        result = [
            {
                "date": point.date,
                "expense_amount": point.expense_amount,
                "non_expense_amount": point.non_expense_amount,
                "difference": point.non_expense_amount - point.expense_amount,
            }
            for point in timeline
        ]
        serializer = AmortizationTimelineSerializer(result, many=True)
        return Response(serializer.data)


def _period(request) -> Period:
    input_serializer = StatisticsInputSerializer(data=request.query_params)
    input_serializer.is_valid(raise_exception=True)
    return Period(
        start=input_serializer.validated_data["start_date"],
        end=input_serializer.validated_data["end_date"],
    )


def _up_to_date_statistics(request) -> DatabaseStatistics | DecryptedStatistics:
    """The statistics of the user, once all their expenses are converted."""
    crypto_key = request.COOKIES.get("user_crypto_key")
    try:
        populate_favourite_currency_amounts(request.user, crypto_key)
        return statistics_for(request.user, crypto_key)
    except MissingCryptoKey:
        raise ValidationError("Missing encryption password in cookie 'user_crypto_key'")


def _trip_statistics(totals: TripTotals | None) -> dict:
    totals = totals or TripTotals()
    duration = 0
    if totals.start_date and totals.end_date:
        duration = (totals.end_date - totals.start_date).days + 1
    return {
        "amount_in_dates": totals.amount_in_dates,
        "total_amount": totals.total_amount,
        "start_date": totals.start_date,
        "end_date": totals.end_date,
        "duration": duration,
        "price_per_day": totals.total_amount / duration if duration else None,
    }
