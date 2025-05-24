from django.urls import path
from .views import ClinicalDecisionSupportAPIView, PatientClinicalHistoryAPIView

urlpatterns = [
    path('api/clinical-decision/', ClinicalDecisionSupportAPIView.as_view(), name='clinical-decision'),
    path('api/clinical-history/', PatientClinicalHistoryAPIView.as_view(), name='clinical-history'),
]