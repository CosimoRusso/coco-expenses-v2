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


def friends_of(user: User) -> models.QuerySet[User]:
    """Users linked to `user` by a Friend row, on either side."""
    is_friend = models.Q(friends_1__user_2=user) | models.Q(friends_2__user_1=user)
    return User.objects.filter(is_friend).distinct()
