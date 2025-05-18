from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from expenses import date_utils
from expenses.constants import TOKEN_DURATION
from expenses.models import User
from expenses.models.token import Token
from expenses.serializers.users import LoginSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action == "login":
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
        if user.check_password(password):
            token = Token.objects.create(
                user=user, expiration_date=date_utils.now() + TOKEN_DURATION
            )
            response = Response({"status": "ok"})
            response.set_cookie(
                key="token", value=token.token, expires=token.expiration_date
            )
            return response
        else:
            raise PermissionDenied("Password incorrect")

    @action(detail=False, methods=["get"])
    def self(self, request, *args, **kwargs):
        user = self.request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)
