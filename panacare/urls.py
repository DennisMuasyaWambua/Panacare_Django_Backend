"""
URL configuration for panacare project.
"""
from django.contrib import admin
from django.urls import path, include

# Import views
from users.views import (
    RoleListAPIView, RoleDetailAPIView,
    UserListAPIView, UserDetailAPIView, UserRegisterAPIView, UserLoginAPIView, UserActivateAPIView,
    CustomerListAPIView, CustomerDetailAPIView
)
from doctors.views import DoctorViewSet
from healthcare.views import HealthCareViewSet

# For the doctor and healthcare apps - keeping viewsets temporarily
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'doctors', DoctorViewSet)
router.register(r'healthcare', HealthCareViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Users app - APIView based URLs
    path('api/roles/', RoleListAPIView.as_view(), name='role-list'),
    path('api/roles/<uuid:pk>/', RoleDetailAPIView.as_view(), name='role-detail'),
    
    path('api/users/', UserListAPIView.as_view(), name='user-list'),
    path('api/users/<uuid:pk>/', UserDetailAPIView.as_view(), name='user-detail'),
    path('api/users/register/', UserRegisterAPIView.as_view(), name='user-register'),
    path('api/users/login/', UserLoginAPIView.as_view(), name='user-login'),
    path('api/users/activate/<str:uidb64>/<str:token>/', UserActivateAPIView.as_view(), name='user-activate'),
    
    path('api/customers/', CustomerListAPIView.as_view(), name='customer-list'),
    path('api/customers/<uuid:pk>/', CustomerDetailAPIView.as_view(), name='customer-detail'),
    
    # For the doctor and healthcare apps - keeping viewsets temporarily
    path('api/', include(router.urls)),
    
    # Django REST framework auth
    path('api-auth/', include('rest_framework.urls')),
]