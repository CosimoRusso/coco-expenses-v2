from expenses.models import User
from expenses.models.token import Token
from rest_framework import authentication
from rest_framework.request import Request


def authenticated_user(request: Request) -> User:
    """The user of a request that went through CustomTokenAuthentication."""
    user = request.user
    assert isinstance(user, User)
    return user


class CustomTokenAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request: Request) -> tuple[User, None] | None:
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
