from django.http import Http404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from expenses import date_utils
from expenses.constants import TOKEN_DURATION
from expenses.models import User
from expenses.models.token import Token
from expenses.serializers.users import LoginSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()

    @action
    def login(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        user = User.objects.filter(email=email).first()
        if user is None:
            raise Http404("User not found")
        if user.check_password(password):
            token = Token.objects.create(
                user=user, expiration_date=date_utils.now() + TOKEN_DURATION
            )
            return Response({"token": token.token})
