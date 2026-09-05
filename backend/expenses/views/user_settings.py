from django.db import transaction
from expenses import date_utils
from expenses.constants import TOKEN_DURATION
from expenses.models import UserSettings
from expenses.serializers.user_settings import (
    UserActivateEncryptionSerializer,
    UserSettingsSerializer,
)
from expenses.utils.encryption.encryption import (
    derive_key_from_password,
    encrypt_user_data,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class UserSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = UserSettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserSettings.objects.filter(user=self.request.user)

    @action(detail=False, methods=["get"])
    def self(self, request, *args, **kwargs):
        user = self.request.user
        user_settings, _ = UserSettings.objects.get_or_create(user=user)
        serializer = self.get_serializer(user_settings)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        user_settings, _ = UserSettings.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(user_settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, methods=["post"])
    def activate_encryption(self, request, *args, **kwargs):
        user_settings, _ = UserSettings.objects.get_or_create(user=request.user)
        if user_settings.is_encrypted:
            return Response(
                {"detail": "Encryption is already activated."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = UserActivateEncryptionSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        with transaction.atomic():
            user_settings.is_encrypted = True
            user_settings.save()
            encrypt_user_data(request.user, validated_data["password"])
        user_crypto_key = derive_key_from_password(
            validated_data["password"], request.user.id
        )
        response = Response(
            {"detail": "Encryption activated successfully."}, status=status.HTTP_200_OK
        )
        expiration_date = date_utils.now() + TOKEN_DURATION
        response.set_cookie(
            key="user_crypto_key",
            value=user_crypto_key,
            expires=expiration_date,
        )
        return response
