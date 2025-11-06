class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ["id", "code", "symbol", "display_name"]
        read_only_fields = ["id", "code", "symbol", "display_name"]