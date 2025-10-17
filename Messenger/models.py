from django.db import models
from django.core.validators import MinValueValidator
from NoGraph import settings
from Channels.models import Channel


class Post(models.Model):
    """帖子模型"""

    POST_TYPES = [
        ('text', '文本'),
        ('vote', '投票'),
        #('image', '图片'),
        ('file', '文件'),
    ]

    id = models.AutoField(primary_key=True)
    in_channel_id = models.PositiveIntegerField(
        verbose_name="频道内ID",
        help_text="帖子在频道内的唯一ID"
    )
    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        verbose_name="所属频道",
        related_name="posts"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="发送者",
        related_name="posts"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    post_type = models.CharField(
        max_length=10,
        choices=POST_TYPES,
        default='text',
        verbose_name="帖子类型"
    )

    class Meta:
        verbose_name = "帖子"
        verbose_name_plural = "帖子"
        ordering = ['-created_at']
        unique_together = ['channel', 'in_channel_id']
        indexes = [
            models.Index(fields=['channel', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
            models.Index(fields=['post_type']),
        ]

    def __str__(self):
        return f"{self.channel.name} - {self.in_channel_id} ({self.sender.username})"

    def get_content(self):
        """获取帖子内容"""
        if hasattr(self, 'plain'):
            return self.plain.content
        return "无内容"

    def get_votes(self):
        """获取投票信息"""
        if hasattr(self, 'vote'):
            return {
                'supporting': self.vote.supporting_votes,
                'opposing': self.vote.opposing_votes,
                'total': self.vote.supporting_votes + self.vote.opposing_votes
            }
        return None


class Plain(models.Model):
    """纯文本内容模型"""

    post = models.OneToOneField(
        Post,
        on_delete=models.CASCADE,
        verbose_name="关联帖子",
        related_name="plain"
    )
    content = models.TextField(
        verbose_name="内容",
        help_text="帖子的文本内容"
    )

    class Meta:
        verbose_name = "文本内容"
        verbose_name_plural = "文本内容"

    def __str__(self):
        preview = self.content[:50] + '...' if len(self.content) > 50 else self.content
        return f"{self.post.channel.name} - {preview}"


class Vote(models.Model):
    """投票模型"""

    post = models.OneToOneField(
        Post,
        on_delete=models.CASCADE,
        verbose_name="关联帖子",
        related_name="vote"
    )
    description = models.TextField(
        verbose_name="描述",
        help_text="投票的描述"
    )
    supporting_votes = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="支持票数"
    )
    opposing_votes = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="反对票数"
    )
    voted_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name="投票用户",
        related_name="voted_usrs"
    )

    class Meta:
        verbose_name = "投票"
        verbose_name_plural = "投票"

    def __str__(self):
        return f"{self.post.channel.name} - 支持:{self.supporting_votes} 反对:{self.opposing_votes}"

    @property
    def total_votes(self):
        """总投票数"""
        return self.supporting_votes + self.opposing_votes

    @property
    def support_rate(self):
        """支持率"""
        channel = Channel.objects.get(id=self.post.channel.id)
        channel_members = channel.members.count()
        if self.total_votes == 0:
            return 0
        elif self.total_votes<=channel_members:
            return self.supporting_votes / channel_members * 100
        else:
            return self.supporting_votes / self.total_votes * 100

    def add_supporting_vote(self):
        """添加支持票"""
        self.supporting_votes += 1
        self.save()

    def add_opposing_vote(self):
        """添加反对票"""
        self.opposing_votes += 1
        self.save()
