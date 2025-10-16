from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display
from Channels.models import Channel

@admin.register(Channel)
class ChannelAdmin(ModelAdmin):
    list_display = ('name', 'get_members_count', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name',)
    filter_horizontal = ('members',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('基本信息', {
            'fields': ('name',),
            'classes': ('wide',),
        }),
        ('成员管理', {
            'fields': ('members',),
            'classes': ('wide',),
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @display(description='成员数量', ordering='members__count')
    def get_members_count(self, obj):
        return obj.members.count()

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('members')
