from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from unfold.admin import ModelAdmin
from unfold.decorators import display
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin, ModelAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'get_full_name_display', 'is_active', 'is_staff', 'is_superuser', 'get_last_login', 'created_at')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'created_at', 'last_login')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login', 'created_at', 'updated_at')

    fieldsets = (
        ('基本信息', {
            'fields': ('username', 'password'),
            'classes': ('wide',),
        }),
        ('个人信息', {
            'fields': ('first_name', 'last_name', 'email'),
            'classes': ('wide',),
        }),
        ('权限管理', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('wide',),
        }),
        ('重要日期', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    add_fieldsets = (
        ('创建用户', {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
        ('权限设置', {
            'classes': ('wide',),
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),
    )

    @display(description='全名', ordering='first_name')
    def get_full_name_display(self, obj):
        if obj.first_name or obj.last_name:
            return f"{obj.first_name} {obj.last_name}".strip()
        return "-"

    @display(description='最后登录', ordering='last_login')
    def get_last_login(self, obj):
        if obj.last_login:
            return obj.last_login.strftime('%Y-%m-%d %H:%M')
        return "从未登录"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()
