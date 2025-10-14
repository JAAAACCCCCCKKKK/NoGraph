from django.contrib.auth.models import User
from django.db import models
from Channels.models import Channel


def post_type_choices():
    """
    Returns a list of tuples representing the choices for post types.
    Each tuple contains an integer identifier and a string description.
    @return: List of tuples for post type choices.
    """
    return [
        (1, 'plain'),
        (2, 'vote'),
    ]


# Create your models here.
class post(models.Model):
    """
    Model representing a post in a channel.
    @param id: Primary key for the post.
    @param in_channel_id: Unique identifier for the post within the channel.
    @param channel: Foreign key linking to the Channel model.
    @param sender: Foreign key linking to the User model who created the post.
    @param created_at: Timestamp when the post was created.
    @param post_type: Type of the post (e.g., 'plain', 'vote
    """
    id = models.BigAutoField(primary_key=True)
    in_channel_id = models.IntegerField(unique=True)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.JSONField(blank=True, null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    post_type = models.IntegerField(choices=post_type_choices(), default=1)


class plain(models.Model):
    """
    Model representing a plain text post.
    @param post: Foreign key linking to the post model.
    @param content: Text content of the post.
    """
    post = models.ForeignKey(post, on_delete=models.CASCADE)
    content = models.TextField()


class vote(models.Model):
    """
    Model representing a voting post.
    @param post: Foreign key linking to the post model.
    @param supporting_votes: Number of supporting votes.
    @param opposing_votes: Number of opposing votes.
    """
    post = models.ForeignKey(post, on_delete=models.CASCADE)
    supporting_votes = models.IntegerField(default=0)
    opposing_votes = models.IntegerField(default=0)
