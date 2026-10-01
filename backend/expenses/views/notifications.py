from django.utils import timezone
from expenses.models import Notification
from expenses.serializers.notifications import NotificationSerializer
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

SHARED_EXPENSE_PARTICIPANT = "sharedexpensenotification_set__shared_expense_participant"


class NotificationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        return (
            Notification.objects.filter(user=self.request.user)
            .select_related(
                "shared_expense_modified__shared_expense",
                "shared_expense_modified__modified_by",
                "shared_expense_deleted__deleted_by",
            )
            .prefetch_related(
                f"{SHARED_EXPENSE_PARTICIPANT}__shared_expense__created_by",
                f"{SHARED_EXPENSE_PARTICIPANT}__expense_set",
            )
            .order_by("-created_at", "-id")
        )

    @action(detail=True, methods=["post"])
    def read(self, request, *args, **kwargs):
        """Mark the notification as read, keeping the first time it was read."""
        notification = self.get_object()
        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=["read_at", "updated_at"])
        return Response(self.get_serializer(notification).data)

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request, *args, **kwargs):
        count = Notification.objects.filter(user=request.user, read_at=None).count()
        return Response({"count": count})
