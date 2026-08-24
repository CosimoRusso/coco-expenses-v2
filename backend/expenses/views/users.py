from django.conf import settings
from expenses import date_utils
from expenses.constants import TOKEN_DURATION
from expenses.models import User
from expenses.models.token import Token
from expenses.models.user_settings import UserSettings
from expenses.serializers.users import (
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)
from expenses.utils.encryption.encryption import derive_key_from_password
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ["login", "register"]:
            return [AllowAny()]
        elif self.action in ["logout", "self"]:
            return [IsAuthenticated()]
        else:
            return [IsAdminUser()]

    @action(detail=False, methods=["post"])
    def login(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        user = User.objects.filter(email=email).first()
        if user is None:
            raise PermissionDenied("User not found")
        if not user.email_confirmed_at or user.email_confirmed_at > date_utils.now():
            raise PermissionDenied("Email not confirmed")
        if not user.check_password(password):
            raise PermissionDenied("Password incorrect")
        token = Token.objects.create(
            user=user, expiration_date=date_utils.now() + TOKEN_DURATION
        )
        response = Response(
            {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": email,
            }
        )
        response.set_cookie(
            key="token", value=token.token, expires=token.expiration_date
        )
        user_settings = UserSettings.objects.get_or_create(user=user)[0]
        if user_settings.is_encrypted:
            user_crypto_key = derive_key_from_password(password, user.id)
            response.set_cookie(
                key="user_crypto_key",
                value=user_crypto_key,
                expires=token.expiration_date,
            )
        return response

    @action(detail=False, methods=["post"])
    def register(self, request, *args, **kwargs):
        if not settings.ALLOW_REGISTRATION:
            raise PermissionDenied("Registration is disabled")
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def logout(self, request, *args, **kwargs):
        user = request.user
        Token.objects.filter(user=user, token=request.COOKIES.get("token")).delete()
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie("token")
        return response

    @action(detail=False, methods=["get"])
    def self(self, request, *args, **kwargs):
        user = self.request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)
