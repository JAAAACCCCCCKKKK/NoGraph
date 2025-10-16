from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class CustomUser(AbstractUser):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    password = models.CharField(max_length=128, blank=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username
