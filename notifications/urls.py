from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for viewsets
router = DefaultRouter()
router.register(r'notifications', views.NotificationViewSet, basename='notifications')
router.register(r'topics', views.TopicSubscriptionViewSet, basename='topic-subscriptions')

urlpatterns = [
    # FCM token registration
    path('fcm/register/token/', views.register_fcm_token, name='register_fcm_token'),
    
    # Include router URLs
    path('', include(router.urls)),
]