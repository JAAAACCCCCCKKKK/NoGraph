from NoGraph import settings
from django.db import models
from django.core.validators import MinLengthValidator


# Create your models here.
class Channel(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=100,
        unique=True,
        validators=[MinLengthValidator(2)],
        verbose_name="频道名称",
        help_text="频道的唯一名称，至少2个字符"
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        verbose_name="成员",
        help_text="频道成员列表"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "频道"
        verbose_name_plural = "频道"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.name} (ID: {self.id})"

    def get_member_count(self):
        """获取成员数量"""
        return self.members.count()

    def is_member(self, user):
        """检查用户是否为频道成员"""
        return self.members.filter(id=user.id).exists()
