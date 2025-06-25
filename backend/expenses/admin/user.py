from django.contrib import admin
from expenses.models import User


class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "last_name", "email_confirmed_at")
    search_fields = ("email", "first_name", "last_name")
    list_filter = ("email_confirmed_at",)
    readonly_fields = ("password_hash",)
    fieldsets = (
        (None, {"fields": ("email", "password_hash")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Status", {"fields": ("email_confirmed_at",)}),
    )
    ordering = ("email",)
