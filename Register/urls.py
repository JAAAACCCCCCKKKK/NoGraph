from django.urls import path
from . import views

app_name = 'register'

urlpatterns = [
    path('verify/', views.Register, name='register'),
    path('sendcode/', views.SendCode, name='sendcode'),
    path('logout/', views.Logout, name='logout'),
]
