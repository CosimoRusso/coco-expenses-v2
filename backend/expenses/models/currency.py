from django.db import models


class Currency(models.Model):
    code = models.CharField(max_length=10)
    symbol = models.CharField(max_length=10)
    display_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.display_name} ({self.code})"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["code"], name="unique_currency_code"),
        ]
