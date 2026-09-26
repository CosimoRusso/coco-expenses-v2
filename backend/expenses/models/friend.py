from django.db import models
from expenses.models.user import User


class Friend(models.Model):
    user_1: User = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=False,
        blank=False,
        related_name="friends_1",
    )
    user_2: User = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=False,
        blank=False,
        related_name="friends_2",
    )
