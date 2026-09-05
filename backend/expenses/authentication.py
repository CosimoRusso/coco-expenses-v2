from typing import Tuple

from expenses.models import User
from expenses.models.token import Token
from rest_framework import authentication, exceptions
from rest_framework.request import Request


class CustomTokenAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request: Request) -> Tuple[User, None]:
        token = request.COOKIES.get("token")
        if not token:
            return None
        try:
            token = Token.objects.get(token=token)
            user = token.user
            # The extension of the expiration date is handled by the SessionRefreshMiddleware
        except Token.DoesNotExist:
            return None

        return user, None

    def authenticate_header(self, request):
        return 'XXXBasic realm="API"'
