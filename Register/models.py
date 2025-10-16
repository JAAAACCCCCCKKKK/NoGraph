from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import EmailValidator


class CustomUser(AbstractUser):
    """自定义用户模型"""

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="激活状态",
        help_text="用户是否激活"
    )
    password = models.CharField(
        max_length=128,
        blank=True,
        verbose_name="密码"
    )
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        verbose_name="邮箱地址",
        help_text="用户的唯一邮箱地址"
    )

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.username} ({self.email})"

    def get_full_name(self):
        """获取完整姓名"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    def get_short_name(self):
        """获取简短姓名"""
        return self.first_name or self.username

    @property
    def is_admin(self):
        """检查是否为管理员"""
        return self.is_staff or self.is_superuser

    def get_posts_count(self):
        """获取用户发帖数量"""
        return self.posts.count()

    def get_channels_count(self):
        """获取用户加入的频道数量"""
        return self.channel_set.count()
