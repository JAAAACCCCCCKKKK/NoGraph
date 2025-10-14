from django.urls import path
from . import views

app_name = 'messenger'

urlpatterns = [
   path('send/', views.send_message, name='send_message')
]