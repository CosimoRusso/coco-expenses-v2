from django.contrib import admin


class SettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "max_categories", "max_trips")
    fields = ("max_categories", "max_trips")
