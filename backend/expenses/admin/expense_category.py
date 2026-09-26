from django.contrib import admin


class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "name", "for_expense", "is_active")
    search_fields = ("user__email", "code", "name")
    list_filter = ("for_expense", "is_active")
    autocomplete_fields = ("user",)
    ordering = ("user__email", "code")
