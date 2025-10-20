from typing import Tuple

from rest_framework import authentication
from rest_framework import exceptions
from rest_framework.request import Request

from expenses.models import User
from expenses.models.token import Token


class CustomTokenAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request: Request) -> Tuple[User, None]:
        token = request.COOKIES.get("token")
        if not token:
            return None
        try:
            token = Token.objects.get(token=token)
            user = token.user
            token.extend_expiration_date()
        except Token.DoesNotExist:
            return None

        return user, None

    def authenticate_header(self, request):
        return 'XXXBasic realm="API"'
