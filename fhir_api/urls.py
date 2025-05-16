from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'Patient', views.FHIRPatientViewSet, basename='fhir-patient')
router.register(r'Practitioner', views.FHIRPractitionerViewSet, basename='fhir-practitioner')
router.register(r'Organization', views.FHIROrganizationViewSet, basename='fhir-organization')
router.register(r'Encounter', views.FHIREncounterViewSet, basename='fhir-encounter')

urlpatterns = [
    # FHIR metadata endpoint
    path('metadata', views.fhir_metadata, name='fhir-metadata'),
    
    # Router URLs
    path('', include(router.urls)),
]