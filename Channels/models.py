from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class Channel(models.Model):
    channel_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    members = models.ManyToManyField(User)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"Channel number: {self.id}, name: {self.name}"

