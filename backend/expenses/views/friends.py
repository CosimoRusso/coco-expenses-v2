from django.db.models import Q
from expenses.models import User
from expenses.serializers.friends import FriendSerializer
from rest_framework import mixins, permissions, viewsets


class FriendViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FriendSerializer

    def get_queryset(self):
        """Users linked to the current user by a Friend row, on either side."""
        user = self.request.user
        is_friend = Q(friends_1__user_2=user) | Q(friends_2__user_1=user)
        return (
            User.objects.filter(is_friend)
            .distinct()
            .order_by("first_name", "last_name", "id")
        )
