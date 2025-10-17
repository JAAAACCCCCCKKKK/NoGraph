from django.urls import path
from . import views

app_name = 'messenger'

urlpatterns = [
   path('send/', views.send_message, name='send_message'),
   path('vote/', views.make_vote, name='make_vote')
]