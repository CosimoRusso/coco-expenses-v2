from typing import Tuple

from rest_framework import authentication
from rest_framework import exceptions

from expenses.models import User
from expenses.models.token import Token


class CustomTokenAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request) -> Tuple[User, None]:
        token = request.META.get("Authorization")
        if not token:
            return None

        try:
            token = token.replace("Bearer ", "")
            token = Token.objects.get(token=token)
            user = token.user
            token.extend_expiration_date()
        except Token.DoesNotExist:
            raise exceptions.AuthenticationFailed("Token not found")

        return user, None
