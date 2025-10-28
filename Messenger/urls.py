from django.urls import path
from . import views

app_name = 'messenger'

urlpatterns = [
   path('send/', views.send_message, name='send_message'),
   path('vote/', views.make_vote, name='make_vote'),
   path('get/', views.get_messages, name='get_messages'),
   path('report/', views.report_message, name='report_post'),
   path('unreport/', views.unreport_message, name='unreport_post'),
]