from django.contrib import admin


class SharedExpenseModifiedNotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "notification",
        "shared_expense",
        "modified_by",
        "amount_before",
        "amount_after",
        "created_at",
    )
    search_fields = ("notification__user__email", "shared_expense__description")
    autocomplete_fields = ("notification", "shared_expense", "modified_by")
    readonly_fields = ("created_at", "updated_at")
