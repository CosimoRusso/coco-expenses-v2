from django.contrib import admin


class SharedExpenseNotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "notification", "shared_expense_participant", "created_at")
    search_fields = (
        "notification__user__email",
        "shared_expense_participant__shared_expense__description",
    )
    autocomplete_fields = ("notification", "shared_expense_participant")
    readonly_fields = ("created_at", "updated_at")
