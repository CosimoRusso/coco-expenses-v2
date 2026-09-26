from django.contrib import admin


class FriendAdmin(admin.ModelAdmin):
    list_display = ("id", "user_1", "user_2")
    search_fields = ("user_1__email", "user_2__email")
    autocomplete_fields = ("user_1", "user_2")
