from django.contrib import admin


class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("code", "symbol", "display_name")
    search_fields = ("code", "symbol", "display_name")
    list_filter = ("code",)
