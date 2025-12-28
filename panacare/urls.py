"""
URL configuration for panacare project.
"""
import os
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

# Import views
from users.views import (
    RoleListAPIView, RoleDetailAPIView,
    UserListAPIView, UserDetailAPIView, UserRegisterAPIView, UserLoginAPIView, UserActivateAPIView,
    PatientListAPIView, PatientDetailAPIView, PatientProfileAPIView, UserProfileAPIView, register_admin_user,
    ResendVerificationAPIView, PasswordChangeAPIView, EmailChangeAPIView, PhoneChangeAPIView,
    ContactUsAPIView, SupportRequestAPIView, ForgotPasswordAPIView, ResetPasswordAPIView, AuditLogViewSet,
    CountiesListAPIView, SubCountiesListAPIView, WardsListAPIView, VillagesListAPIView,
    LocationHierarchyAPIView, SyncLocationsAPIView, CHPPatientCreateAPIView, CHPClinicalDecisionSupportAPIView,
    CHPDoctorAvailabilityAPIView, CHPAppointmentBookingAPIView, CHPBatchAppointmentBookingAPIView,
    CHPPatientAppointmentsAPIView, CHPPatientsListAPIView
)
from doctors.views import DoctorViewSet
import doctors.views
from healthcare.views import (
    HealthCareViewSet, AppointmentViewSet, ConsultationViewSet, DoctorRatingViewSet,
    ArticleViewSet, ArticleCommentViewSet, PackageViewSet, PatientSubscriptionViewSet, 
    DoctorAvailabilityViewSet, PaymentViewSet, PackagePaymentTrackerViewSet, RiskSegmentationViewSet,
    TeleconsultationLogViewSet, FollowUpComplianceViewSet, EnhancedAppointmentListViewSet, PatientJournalViewSet
    # AppointmentDocumentViewSet, ResourceViewSet,
)
from rest_framework_simplejwt.views import (
    TokenRefreshView, TokenVerifyView
)
import panacare.utils
import panacare.test_cors

# Swagger documentation
from rest_framework import permissions
from django.conf import settings
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
   openapi.Info(
      title="Panacare API",
      default_version='v1',
      description="""
      API documentation for Panacare Healthcare System
      
      ## Authentication
      
      Most endpoints require authentication with a JWT token. 
      To authenticate, include the token in the Authorization header as follows:
      
      `Authorization: Bearer <your_token>`
      
      Tokens can be obtained through the login endpoint: `POST /api/users/login/`
      
      ## FHIR Compliance
      
      All GET endpoints support FHIR format responses by adding the `format=fhir` query parameter.
      
      Example: `GET /api/patients/?format=fhir`
      
      The response will follow FHIR R4 (4.0.1) standards with appropriate resource types.
      
      ## Response Formats
      
      The API returns data in JSON format by default. Responses typically follow this structure:
      
      ```json
      {
          "status": "success",  // or "error"
          "data": { ... },     // The requested data, or null in case of error
          "message": "...",   // Human-readable message
          "errors": { ... }    // Validation errors if applicable
      }
      ```
      
      ## Error Handling
      
      The API uses standard HTTP status codes to indicate the success or failure of requests:
      
      - 200: Success
      - 201: Created
      - 400: Bad Request
      - 401: Unauthorized
      - 403: Forbidden
      - 404: Not Found
      - 500: Server Error
      """,
      terms_of_service="https://www.panacare.com/terms/",
      contact=openapi.Contact(email="contact@panacare.com"),
      license=openapi.License(name="MIT License"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

# For the doctor and healthcare apps - keeping viewsets temporarily
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'doctors', DoctorViewSet, basename='doctor')
router.register(r'healthcare', HealthCareViewSet, basename='healthcare')
# router.register(r'doctor-availability/<uuid:doctor_id>/', DoctorAvailabilityViewSet, basename='doctor-availability')
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'doctor-availability', DoctorAvailabilityViewSet, basename='doctor-availability')
router.register(r'consultations', ConsultationViewSet, basename='consultation')
router.register(r'packages', PackageViewSet, basename='package')
router.register(r'subscriptions', PatientSubscriptionViewSet, basename='subscription')
router.register(r'payments', PaymentViewSet, basename='payment')
# router.register(r'resources', ResourceViewSet, basename='resource')
router.register(r'doctor-ratings', DoctorRatingViewSet, basename='doctor-rating')
router.register(r'articles', ArticleViewSet, basename='article')
router.register(r'article-comments', ArticleCommentViewSet, basename='article-comment')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')
router.register(r'package-payment-tracker', PackagePaymentTrackerViewSet, basename='package-payment-tracker')
router.register(r'risk-segmentation', RiskSegmentationViewSet, basename='risk-segmentation')
router.register(r'teleconsultation-logs', TeleconsultationLogViewSet, basename='teleconsultation-log')
router.register(r'follow-up-compliance', FollowUpComplianceViewSet, basename='follow-up-compliance')
router.register(r'enhanced-appointments', EnhancedAppointmentListViewSet, basename='enhanced-appointments')
router.register(r'patient-journals', PatientJournalViewSet, basename='patient-journal')

# doctor_availability_create = DoctorAvailabilityViewSet.as_view({
#     'post': 'create'
# })
router_urls = router.urls
# Note: These URLs are automatically generated by the router and the @action decorator
admin_urls = [
    # Doctor endpoints
    path('api/doctors/admin_add_doctor/', DoctorViewSet.as_view({'post': 'admin_add_doctor'}), name='admin-add-doctor'),
    path('api/doctors/admin_list_doctors/', DoctorViewSet.as_view({'get': 'admin_list_doctors'}), name='admin-list-doctors'),
    path('api/doctors/admin_view_doctor/<uuid:pk>/', DoctorViewSet.as_view({'get': 'admin_view_doctor'}), name='admin-view-doctor'),
    path('api/doctor-availability/<uuid:doctor_id>/', DoctorAvailabilityViewSet.as_view({'get': 'list'}), name='doctor-availability-by-doctor'),
    path('api/doctors/admin_list_patients/', DoctorViewSet.as_view({'get': 'admin_list_patients'}), name='admin-list-patients'),
    path('api/doctors/admin_view_patient/<uuid:pk>/', DoctorViewSet.as_view({'get': 'admin_view_patient'}), name='admin-view-patient'),
    path('api/doctors/<uuid:pk>/verify/', DoctorViewSet.as_view({'patch': 'verify_doctor'}), name='verify-doctor'),
    path('api/doctors/add_profile/', doctors.views.add_doctor_profile, name='add-doctor-profile'),
    path('api/doctors/profile/', DoctorViewSet.as_view({'get': 'profile'}), name='doctor-profile'),
    
    # Healthcare endpoints for patient-doctor assignments
    path('api/healthcare/assign_patient_to_doctor/', HealthCareViewSet.as_view({'post': 'assign_patient_to_doctor'}), name='assign-patient-to-doctor'),
    path('api/healthcare/list_patient_doctor_assignments/', HealthCareViewSet.as_view({'get': 'list_patient_doctor_assignments'}), name='list-patient-doctor-assignments'),
    path('api/healthcare/view_assignment/<uuid:pk>/', HealthCareViewSet.as_view({'get': 'view_assignment'}), name='view-assignment'),
    path('api/healthcare/doctor/patients/', HealthCareViewSet.as_view({'get': 'doctor_assigned_patients'}), name='doctor-assigned-patients'),
    path('api/healthcare/doctor/patient/<uuid:pk>/', HealthCareViewSet.as_view({'get': 'doctor_view_patient'}), name='doctor-view-patient'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Documentation with Swagger - make paths more explicit and straightforward
    path('', RedirectView.as_view(url='/swagger/', permanent=False), name='index'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger.yaml', schema_view.without_ui(cache_timeout=0), name='schema-yaml'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Users app - APIView based URLs
    path('api/roles/', RoleListAPIView.as_view(), name='role-list'),
    path('api/roles/<uuid:pk>/', RoleDetailAPIView.as_view(), name='role-detail'),
    
    path('api/users/', UserListAPIView.as_view(), name='user-list'),
    path('api/users/<uuid:pk>/', UserDetailAPIView.as_view(), name='user-detail'),
    path('api/users/register/', UserRegisterAPIView.as_view(), name='user-register'),
    path('api/users/login/', UserLoginAPIView.as_view(), name='user-login'),
    path('api/users/activate/<str:uidb64>/<str:token>/', UserActivateAPIView.as_view(), name='user-activate'),
    path('api/users/register-admin/', register_admin_user, name='register-admin'),
    
    # Authentication endpoints
    path('api/users/resend-verification/', ResendVerificationAPIView.as_view(), name='resend-verification'),
    path('api/users/change-password/', PasswordChangeAPIView.as_view(), name='change-password'),
    path('api/users/change-email/', EmailChangeAPIView.as_view(), name='change-email'),
    path('api/users/change-phone/', PhoneChangeAPIView.as_view(), name='change-phone'),
    path('api/contact-us/', ContactUsAPIView.as_view(), name='contact-us'),
    path('api/support-request/', SupportRequestAPIView.as_view(), name='support-request'),
    path('api/forgot-password/', ForgotPasswordAPIView.as_view(), name='forgot-password'),
    path('api/reset-password/<str:uidb64>/<str:token>/', ResetPasswordAPIView.as_view(), name='reset-password'),
    
    # Profile endpoints
    path('api/patient/profile/', PatientProfileAPIView.as_view(), name='patient-profile'),
    path('api/profile/', UserProfileAPIView.as_view(), name='user-profile'),
    
    path('api/patients/', PatientListAPIView.as_view(), name='patient-list'),
    path('api/patients/<uuid:pk>/', PatientDetailAPIView.as_view(), name='patient-detail'),
    
    # Location endpoints for hierarchical dropdowns
    path('api/locations/counties/', CountiesListAPIView.as_view(), name='counties-list'),
    path('api/locations/subcounties/', SubCountiesListAPIView.as_view(), name='subcounties-list'),
    path('api/locations/wards/', WardsListAPIView.as_view(), name='wards-list'),
    path('api/locations/villages/', VillagesListAPIView.as_view(), name='villages-list'),
    path('api/locations/hierarchy/', LocationHierarchyAPIView.as_view(), name='location-hierarchy'),
    path('api/locations/sync/', SyncLocationsAPIView.as_view(), name='sync-locations'),
    
    # Community Health Provider endpoints
    path('api/chp/create-patient/', CHPPatientCreateAPIView.as_view(), name='chp-create-patient'),
    path('api/chp/patients/', CHPPatientsListAPIView.as_view(), name='chp-patients-list'),
    path('api/chp/cdss/', CHPClinicalDecisionSupportAPIView.as_view(), name='chp-cdss'),
    path('api/chp/doctors/', CHPDoctorAvailabilityAPIView.as_view(), name='chp-doctors'),
    path('api/chp/book-appointment/', CHPAppointmentBookingAPIView.as_view(), name='chp-book-appointment'),
    path('api/chp/batch-book-appointments/', CHPBatchAppointmentBookingAPIView.as_view(), name='chp-batch-book-appointments'),
    path('api/chp/appointments/', CHPPatientAppointmentsAPIView.as_view(), name='chp-appointments'),
    
    # Add the admin URLs explicitly
    *admin_urls,
    
    # For the doctor and healthcare apps - keeping viewsets temporarily
    path('api/', include(router.urls)),
    
    # Add token verification endpoint
    path('api/verify-token/', panacare.utils.verify_token_view, name='verify-token'),
    
    # Django REST framework auth
    path('api-auth/', include('rest_framework.urls')),
    
    # JWT Authentication
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # CORS Test endpoint
    path('api/test-cors/', panacare.test_cors.test_cors, name='test-cors'),
    
    # FHIR API
    path('fhir/', include('fhir_api.urls')),
    
    # Clinical Decision Support
    path('', include('clinical_support.urls')),
    
    # FCM Notifications
    path('api/', include('notifications.urls')),
]

# Media files serving in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)