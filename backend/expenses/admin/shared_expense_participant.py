from django.contrib import admin


class SharedExpenseParticipantAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "shared_expense", "quota", "created_at")
    search_fields = ("user__email", "shared_expense__description")
    autocomplete_fields = ("user", "shared_expense")
    readonly_fields = ("created_at", "updated_at")
