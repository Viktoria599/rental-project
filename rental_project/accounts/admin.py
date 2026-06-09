from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('phone', 'city', 'rating', 'balance')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone', 'city', 'rating')