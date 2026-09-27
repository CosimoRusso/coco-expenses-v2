from django.db import models


class PaymentMethod(models.Model):
    user = models.ForeignKey(
        "User", on_delete=models.PROTECT, related_name="payment_methods"
    )
    code = models.CharField(verbose_name="Payment Method", max_length=128)
    name = models.CharField(verbose_name="Payment Method", max_length=128)
    is_active = models.BooleanField(verbose_name="Is Active", default=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        unique_together = ("user", "code")
