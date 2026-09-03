from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'username', 'matric_number', 'department', 'is_email_verified',
                     'reputation_score', 'is_staff')
    list_filter = ('is_email_verified', 'is_staff', 'department')
    search_fields = ('email', 'username', 'department')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Profile', {'fields': ('department', 'matric_number')}),
        ('Verification & trust', {
            'fields': ('is_email_verified', 'reputation_score', 'total_ratings')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser',
                       'groups', 'user_permissions')
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'department', 'password1', 'password2'),
        }),
    )