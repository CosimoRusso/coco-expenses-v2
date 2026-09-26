from expenses.serializers.currencies import CurrencySerializer
from rest_framework import serializers


class MovementSerializer(serializers.Serializer):
    description = serializers.CharField()
    date = serializers.DateField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = CurrencySerializer()


class BalanceSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(source="other.id")
    first_name = serializers.CharField(source="other.first_name")
    last_name = serializers.CharField(source="other.last_name")
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    movements = MovementSerializer(many=True)


class BalancesSerializer(serializers.Serializer):
    currency = CurrencySerializer()
    balances = BalanceSerializer(many=True)
