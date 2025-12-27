from django.contrib import admin


class DollarExchangeRateAdmin(admin.ModelAdmin):
    list_display = ("currency", "date", "rate")
    search_fields = ("currency__code", "currency__display_name", "currency__symbol")
    list_filter = ("currency", "date")
    date_hierarchy = "date"
    ordering = ("-date", "currency")
