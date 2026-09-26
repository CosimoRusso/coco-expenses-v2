from django.contrib import admin


class SharedExpenseDeletedNotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "notification",
        "deleted_by",
        "description",
        "amount",
        "currency",
        "created_at",
    )
    search_fields = ("notification__user__email", "description")
    autocomplete_fields = ("notification", "deleted_by")
    readonly_fields = ("created_at", "updated_at")
