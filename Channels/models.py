from NoGraph import settings
from django.db import models


# Create your models here.
class Channel(models.Model):
    name = models.CharField(max_length=100, primary_key=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"Channel number: {self.id}, name: {self.name}"

