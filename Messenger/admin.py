from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from Messenger.models import Post, Plain, Vote


class PlainInline(TabularInline):
    model = Plain
    extra = 0
    fields = ('content',)


class VoteInline(TabularInline):
    model = Vote
    extra = 0
    fields = ('supporting_votes', 'opposing_votes')


@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = ('id', 'in_channel_id', 'channel', 'sender', 'post_type', 'get_votes_summary', 'created_at')
    list_filter = ('post_type', 'channel', 'created_at')
    search_fields = ('sender__username', 'channel__name', 'plain__content')
    autocomplete_fields = ('sender', 'channel')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    fieldsets = (
        ('基本信息', {
            'fields': ('in_channel_id', 'channel', 'sender', 'post_type'),
            'classes': ('wide',),
        }),
        ('时间戳', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    inlines = [PlainInline, VoteInline]

    @display(description='投票统计', ordering='vote__supporting_votes')
    def get_votes_summary(self, obj):
        try:
            if hasattr(obj, 'vote'):
                vote_obj = obj.vote
                return f"支持: {vote_obj.supporting_votes} | 反对: {vote_obj.opposing_votes}"
            return "无投票"
        except:
            return "无投票"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('channel', 'sender').prefetch_related('vote', 'plain')


@admin.register(Plain)
class PlainAdmin(ModelAdmin):
    list_display = ('post', 'get_post_channel', 'get_post_sender', 'content_preview')
    list_filter = ('post__channel', 'post__created_at')
    search_fields = ('content', 'post__sender__username')
    autocomplete_fields = ('post',)

    fieldsets = (
        ('内容信息', {
            'fields': ('post', 'content'),
            'classes': ('wide',),
        }),
    )

    @display(description='所属频道')
    def get_post_channel(self, obj):
        return obj.post.channel.name if obj.post and obj.post.channel else '-'

    @display(description='发送者')
    def get_post_sender(self, obj):
        return obj.post.sender.username if obj.post and obj.post.sender else '-'

    @display(description='内容预览')
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content


@admin.register(Vote)
class VoteAdmin(ModelAdmin):
    list_display = ('post', 'get_post_channel', 'supporting_votes', 'opposing_votes', 'get_total_votes',
                    'get_vote_ratio')
    list_filter = ('post__channel', 'post__created_at')
    search_fields = ('post__sender__username', 'post__channel__name')
    autocomplete_fields = ('post',)

    fieldsets = (
        ('投票信息', {
            'fields': ('post', 'supporting_votes', 'opposing_votes'),
            'classes': ('wide',),
        }),
    )

    @display(description='所属频道')
    def get_post_channel(self, obj):
        return obj.post.channel.name if obj.post and obj.post.channel else '-'

    @display(description='总票数', ordering='supporting_votes')
    def get_total_votes(self, obj):
        return obj.total_votes

    @display(description='支持率')
    def get_vote_ratio(self, obj):
        return f"{obj.support_rate:.1f}%"
