from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'Patient', views.FHIRPatientViewSet, basename='fhir-patient')
router.register(r'Practitioner', views.FHIRPractitionerViewSet, basename='fhir-practitioner')
router.register(r'Organization', views.FHIROrganizationViewSet, basename='fhir-organization')
router.register(r'Appointment', views.FHIRAppointmentViewSet, basename='fhir-appointment')
router.register(r'Encounter', views.FHIREncounterViewSet, basename='fhir-encounter')
router.register(r'ServiceRequest', views.FHIRServiceRequestViewSet, basename='fhir-servicerequest')
router.register(r'DocumentReference', views.FHIRDocumentReferenceViewSet, basename='fhir-documentreference')
router.register(r'CarePlan', views.FHIRCarePlanViewSet, basename='fhir-careplan')
router.register(r'CareTeam', views.FHIRCareTeamViewSet, basename='fhir-careteam')
router.register(r'Task', views.FHIRTaskViewSet, basename='fhir-task')
router.register(r'Communication', views.FHIRCommunicationViewSet, basename='fhir-communication')
router.register(r'Coverage', views.FHIRCoverageViewSet, basename='fhir-coverage')
router.register(r'Claim', views.FHIRClaimViewSet, basename='fhir-claim')
router.register(r'Consent', views.FHIRConsentViewSet, basename='fhir-consent')
router.register(r'Location', views.FHIRLocationViewSet, basename='fhir-location')

urlpatterns = [
    # FHIR metadata endpoint
    path('metadata', views.fhir_metadata, name='fhir-metadata'),
    
    # Router URLs
    path('', include(router.urls)),
]