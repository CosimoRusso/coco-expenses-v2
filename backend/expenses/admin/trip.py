from django.contrib import admin


class TripAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "name")
    search_fields = ("user__username", "code", "name")
    list_filter = ("user",)
