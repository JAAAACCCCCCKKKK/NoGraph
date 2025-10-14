from django.contrib.auth.models import User
from django.db import models
from Channels.models import *


class Post(models.Model):
    id = models.AutoField(primary_key=True)
    in_channel_id = models.IntegerField(unique=True)
    channel = models.ForeignKey(Channel,on_delete=models.CASCADE,to_field='name')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    tYpe = models.CharField(max_length=10)

class Plain(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    content = models.TextField()

class vote(models.Model):
    Post = models.ForeignKey(Post, on_delete=models.CASCADE)
    supporting_votes = models.IntegerField(default=0)
    opposing_votes = models.IntegerField(default=0)