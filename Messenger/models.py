from django.db import models
from Channels.models import Channel
from Register.models import User

# Create your models here.
class post(models.Model):
    id = models.BigAutoField(primary_key=True)
    in_channel_id = models.BigAutoField(unique=True)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    tYpe = models.CharField(max_length=10)

class plain(models.Model):
    post = models.ForeignKey(post, on_delete=models.CASCADE)
    content = models.TextField()

class vote(models.Model):
    post = models.ForeignKey(post, on_delete=models.CASCADE)
    supporting_votes = models.IntegerField(default=0)
    opposing_votes = models.IntegerField(default=0)