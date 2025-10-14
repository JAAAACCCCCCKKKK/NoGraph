from django.urls import path
from Channels.views import *

app_name = 'channels'

urlpatterns = [
    path('create/', create_channel, name='create_channel'),
]