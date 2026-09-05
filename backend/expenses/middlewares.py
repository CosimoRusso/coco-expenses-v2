from types import SimpleNamespace

from expenses import date_utils
from expenses.constants import TOKEN_DURATION
from expenses.models.token import Token


class SessionRefreshMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Ran after authentication middleware, so request.user is set
        response = self.get_response(request)

        if not (request.user and request.user.is_authenticated):
            return response

        # User is authenticated, from here we can assume we have a cookie and that it is valid.
        # We extend the session and the user_crypto_key (if present) to have the same expiration

        # Search first in the response for the case of a login performed when a cookie
        # already exist in the response: we would discard the new cookie and extend
        # the old one that is not valid anymore
        session_token = response.cookies.get(
            "token", SimpleNamespace(value=None)
        ).value or request.COOKIES.get("token")
        user_crypto_key = response.cookies.get(
            "user_crypto_key", SimpleNamespace(value=None)
        ).value or request.COOKIES.get("user_crypto_key")

        updated_expiration = date_utils.now() + TOKEN_DURATION

        response.set_cookie(
            key="token",
            value=session_token,
            expires=updated_expiration,
        )
        Token.objects.filter(user=request.user, token=session_token).update(
            expiration_date=updated_expiration
        )

        if user_crypto_key:
            response.set_cookie(
                key="user_crypto_key",
                value=user_crypto_key,
                expires=updated_expiration,
            )

        return response
