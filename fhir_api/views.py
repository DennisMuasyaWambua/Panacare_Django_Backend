from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import Patient
from doctors.models import Doctor
from healthcare.models import HealthCare  # , PatientDoctorAssignment

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Define the format parameter for Swagger documentation
format_parameter = openapi.Parameter(
    'format', 
    openapi.IN_QUERY, 
    description="Response format. Set to 'fhir' for FHIR-compliant responses", 
    type=openapi.TYPE_STRING,
    required=False,
    enum=['fhir']
)

from .adapters import (
    create_fhir_patient, 
    create_fhir_practitioner, 
    create_fhir_organization
    # create_fhir_encounter
)
from .serializers import (
    PatientFHIRSerializer,
    PractitionerFHIRSerializer,
    OrganizationFHIRSerializer,
    EncounterFHIRSerializer,
    BundleSerializer,
    create_bundle
)


class FHIRPatientViewSet(viewsets.ViewSet):
    """
    ViewSet for FHIR Patient resources
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Return a list of all patients as FHIR Patient resources",
        responses={200: PatientFHIRSerializer(many=True)}
    )
    def list(self, request):
        """
        Return a list of all patients as FHIR Patient resources
        """
        patients = Patient.objects.all()
        
        # Convert each Patient to a FHIR Patient
        fhir_patients = [create_fhir_patient(patient) for patient in patients]
        
        # Create a Bundle containing all patients
        bundle = create_bundle(fhir_patients)
        
        # Serialize the bundle
        serializer = BundleSerializer(bundle)
        
        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"
        
        return response
    
    @swagger_auto_schema(
        operation_description="Return a single patient as a FHIR Patient resource",
        responses={200: PatientFHIRSerializer()}
    )
    def retrieve(self, request, pk=None):
        """
        Return a single patient as a FHIR Patient resource
        """
        patient = get_object_or_404(Patient, pk=pk)
        
        # Convert Patient to FHIR Patient
        fhir_patient = create_fhir_patient(patient)
        
        # Serialize the FHIR Patient
        serializer = PatientFHIRSerializer(fhir_patient)
        
        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"
        
        return response


class FHIRPractitionerViewSet(viewsets.ViewSet):
    """
    ViewSet for FHIR Practitioner resources
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Return a list of all doctors as FHIR Practitioner resources",
        responses={200: PractitionerFHIRSerializer(many=True)}
    )
    def list(self, request):
        """
        Return a list of all doctors as FHIR Practitioner resources
        """
        doctors = Doctor.objects.all()
        
        # Convert each Doctor to a FHIR Practitioner
        fhir_practitioners = [create_fhir_practitioner(doctor) for doctor in doctors]
        
        # Create a Bundle containing all practitioners
        bundle = create_bundle(fhir_practitioners)
        
        # Serialize the bundle
        serializer = BundleSerializer(bundle)
        
        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"
        
        return response
    
    @swagger_auto_schema(
        operation_description="Return a single doctor as a FHIR Practitioner resource",
        responses={200: PractitionerFHIRSerializer()}
    )
    def retrieve(self, request, pk=None):
        """
        Return a single doctor as a FHIR Practitioner resource
        """
        doctor = get_object_or_404(Doctor, pk=pk)
        
        # Convert Doctor to FHIR Practitioner
        fhir_practitioner = create_fhir_practitioner(doctor)
        
        # Serialize the FHIR Practitioner
        serializer = PractitionerFHIRSerializer(fhir_practitioner)
        
        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"
        
        return response


class FHIROrganizationViewSet(viewsets.ViewSet):
    """
    ViewSet for FHIR Organization resources
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Return a list of all healthcare facilities as FHIR Organization resources",
        responses={200: OrganizationFHIRSerializer(many=True)}
    )
    def list(self, request):
        """
        Return a list of all healthcare facilities as FHIR Organization resources
        """
        facilities = HealthCare.objects.all()
        
        # Convert each HealthCare to a FHIR Organization
        fhir_organizations = [create_fhir_organization(facility) for facility in facilities]
        
        # Create a Bundle containing all organizations
        bundle = create_bundle(fhir_organizations)
        
        # Serialize the bundle
        serializer = BundleSerializer(bundle)
        
        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"
        
        return response
    
    @swagger_auto_schema(
        operation_description="Return a single healthcare facility as a FHIR Organization resource",
        responses={200: OrganizationFHIRSerializer()}
    )
    def retrieve(self, request, pk=None):
        """
        Return a single healthcare facility as a FHIR Organization resource
        """
        facility = get_object_or_404(HealthCare, pk=pk)
        
        # Convert HealthCare to FHIR Organization
        fhir_organization = create_fhir_organization(facility)
        
        # Serialize the FHIR Organization
        serializer = OrganizationFHIRSerializer(fhir_organization)
        
        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"
        
        return response


# class FHIREncounterViewSet(viewsets.ViewSet):
#     """
#     ViewSet for FHIR Encounter resources
#     """
#     permission_classes = [permissions.IsAuthenticated]
#     
#     @swagger_auto_schema(
#         operation_description="Return a list of all patient-doctor assignments as FHIR Encounter resources",
#         responses={200: EncounterFHIRSerializer(many=True)}
#     )
#     def list(self, request):
#         """
#         Return a list of all patient-doctor assignments as FHIR Encounter resources
#         """
#         assignments = PatientDoctorAssignment.objects.all()
#         
#         # Convert each PatientDoctorAssignment to a FHIR Encounter
#         fhir_encounters = [create_fhir_encounter(assignment) for assignment in assignments]
#         
#         # Create a Bundle containing all encounters
#         bundle = create_bundle(fhir_encounters)
#         
#         # Serialize the bundle
#         serializer = BundleSerializer(bundle)
#         
#         # Set appropriate content type for FHIR responses
#         response = Response(serializer.data)
#         response["Content-Type"] = "application/fhir+json"
#         
#         return response
#     
#     @swagger_auto_schema(
#         operation_description="Return a single patient-doctor assignment as a FHIR Encounter resource",
#         responses={200: EncounterFHIRSerializer()}
#     )
#     def retrieve(self, request, pk=None):
#         """
#         Return a single patient-doctor assignment as a FHIR Encounter resource
#         """
#         assignment = get_object_or_404(PatientDoctorAssignment, pk=pk)
#         
#         # Convert PatientDoctorAssignment to FHIR Encounter
#         fhir_encounter = create_fhir_encounter(assignment)
#         
#         # Serialize the FHIR Encounter
#         serializer = EncounterFHIRSerializer(fhir_encounter)
#         
#         # Set appropriate content type for FHIR responses
#         response = Response(serializer.data)
#         response["Content-Type"] = "application/fhir+json"
#         
#         return response
# 
# 
# FHIR metadata endpoint
@swagger_auto_schema(
    method='get',
    operation_description="Return FHIR server capability statement",
    responses={200: "FHIR CapabilityStatement"}
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def fhir_metadata(request):
    """
    Return FHIR server capability statement
    """
    metadata = {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": "2025-05-15",
        "publisher": "Panacare Healthcare",
        "kind": "instance",
        "software": {
            "name": "Panacare FHIR API",
            "version": "1.0.0"
        },
        "implementation": {
            "description": "Panacare Healthcare FHIR API",
            "url": request.build_absolute_uri('/fhir/')
        },
        "fhirVersion": "4.0.1",
        "format": ["json"],
        "rest": [
            {
                "mode": "server",
                "resource": [
                    {
                        "type": "Patient",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"}
                        ],
                        "searchParam": [
                            {"name": "_id", "type": "token"}
                        ]
                    },
                    {
                        "type": "Practitioner",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"}
                        ],
                        "searchParam": [
                            {"name": "_id", "type": "token"}
                        ]
                    },
                    {
                        "type": "Organization",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"}
                        ],
                        "searchParam": [
                            {"name": "_id", "type": "token"}
                        ]
                    },
                    {
                        "type": "Encounter",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"}
                        ],
                        "searchParam": [
                            {"name": "_id", "type": "token"}
                        ]
                    }
                ]
            }
        ]
    }
    
    # Set appropriate content type for FHIR responses
    response = Response(metadata)
    response["Content-Type"] = "application/fhir+json"
    
    return response
