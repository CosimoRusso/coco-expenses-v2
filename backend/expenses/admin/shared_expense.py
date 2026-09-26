from django.contrib import admin
from expenses.models import SharedExpenseParticipant


class SharedExpenseParticipantInline(admin.TabularInline):
    model = SharedExpenseParticipant
    extra = 0
    autocomplete_fields = ("user",)


class SharedExpenseAdmin(admin.ModelAdmin):
    list_display = ("id", "description", "amount", "currency", "created_at")
    search_fields = ("description",)
    list_filter = ("currency",)
    autocomplete_fields = ("currency",)
    readonly_fields = ("created_at", "updated_at")
    inlines = (SharedExpenseParticipantInline,)
