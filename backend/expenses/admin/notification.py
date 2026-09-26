from django.contrib import admin


class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "kind", "read_at", "created_at")
    search_fields = ("user__email",)
    list_filter = ("kind", "read_at")
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "updated_at")
