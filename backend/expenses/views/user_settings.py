from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from expenses.models import UserSettings
from expenses.serializers.user_settings import UserSettingsSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status


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
