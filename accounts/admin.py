from django.contrib import admin

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

class UserAdmin(BaseUserAdmin):
    # 管理画面で表示するカラム
    list_display = ('username', 'display_name', 'email', 'is_staff', 'is_superuser')
    # 検索可能にするフィールド
    search_fields = ('username', 'display_name', 'email')
    # 編集画面で表示するフィールド
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('display_name', 'email', 'icon')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

admin.site.register(User, UserAdmin)
