from django.db import models
from .currency import Currency

class DollarExchangeRate(models.Model):
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    date = models.DateField()
    rate = models.DecimalField(max_digits=14, decimal_places=4)

    def __str__(self):
        return f"{self.date} - {self.rate}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["date", "currency"], name="unique_dollar_exchange_rate_date_currency")
        ]