from django.urls import path
from Messenger.views import *

app_name = 'messenger'

urlpatterns = [
    path('send/', send_message, name='send_message')
]