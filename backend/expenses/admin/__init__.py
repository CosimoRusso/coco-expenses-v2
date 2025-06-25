from django.contrib import admin
from expenses.models import User
from expenses.admin.user import UserAdmin

# Register the User model with the custom UserAdmin
admin.site.register(User, UserAdmin)
