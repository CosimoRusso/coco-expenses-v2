from expenses.models.friend import friends_of
from expenses.serializers.friends import FriendSerializer
from rest_framework import mixins, permissions, viewsets


class FriendViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FriendSerializer

    def get_queryset(self):
        return friends_of(self.request.user).order_by("first_name", "last_name", "id")
