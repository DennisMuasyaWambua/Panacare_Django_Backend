from django.urls import path
from . import views

urlpatterns = [
    path('fcm/register/token/', views.register_fcm_token, name='register_fcm_token'),
]