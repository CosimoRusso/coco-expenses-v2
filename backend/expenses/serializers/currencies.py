from rest_framework import serializers
from expenses.models.currency import Currency

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ["id", "code", "symbol", "display_name"]
        read_only_fields = ["id", "code", "symbol", "display_name"]