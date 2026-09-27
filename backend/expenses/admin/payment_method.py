from django.contrib import admin


class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "name", "is_active")
    search_fields = ("user__email", "code", "name")
    list_filter = ("is_active",)
    autocomplete_fields = ("user",)
    ordering = ("user__email", "code")
