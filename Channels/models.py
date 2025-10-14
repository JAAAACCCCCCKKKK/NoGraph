from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class Channel(models.Model):
    """
    Model representing a communication channel.
    @param id: Primary key for the channel.
    @param name: Name of the channel.
    @param members: Many-to-many relationship with User model representing channel members.
    @param created_at: Timestamp when the channel was created.
    @param updated_at: Timestamp when the channel was last updated.
    """
    id = models.BigAutoField(primary_key=True, unique=True)
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(User, related_name='channels')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"Channel number: {self.id}, name: {self.name}"


