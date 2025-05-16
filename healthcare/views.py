from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import HealthCare, PatientDoctorAssignment
from .serializers import HealthCareSerializer, PatientDoctorAssignmentSerializer
from doctors.views import IsAdminUser
from users.models import User, Role, Patient
from doctors.models import Doctor
from django.shortcuts import get_object_or_404

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

class HealthCareViewSet(viewsets.ModelViewSet):
    queryset = HealthCare.objects.all()
    serializer_class = HealthCareSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="List all healthcare facilities",
        manual_parameters=[
            format_parameter,
            openapi.Parameter('category', openapi.IN_QUERY, type=openapi.TYPE_STRING, 
                            description="Filter by category (GENERAL, PEDIATRIC, MENTAL, DENTAL, VISION, OTHER)"),
            openapi.Parameter('name', openapi.IN_QUERY, type=openapi.TYPE_STRING, 
                            description="Filter by name (contains search)"),
            openapi.Parameter('active', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, 
                            description="Filter by active status")
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
        
    @swagger_auto_schema(
        operation_description="Get details of a specific healthcare facility",
        manual_parameters=[format_parameter]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    def finalize_response(self, request, response, *args, **kwargs):
        """
        Add CORS headers to all responses
        """
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-Requested-With"
        
        # Add FHIR content type header if format is FHIR
        if request.query_params.get('format') == 'fhir':
            response["Content-Type"] = "application/fhir+json"
            
        return response
    
    def get_permissions(self):
        """
        Override to set custom permissions for different actions
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = HealthCare.objects.all()
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        active = self.request.query_params.get('active')
        if active:
            queryset = queryset.filter(is_active=active.lower() == 'true')
        return queryset
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def assign_patient_to_doctor(self, request):
        """
        Endpoint for admin to assign a patient to a doctor
        """
        # Get patient and doctor
        patient_id = request.data.get('patient_id')
        doctor_id = request.data.get('doctor_id')
        notes = request.data.get('notes', '')
        
        if not patient_id or not doctor_id:
            return Response({
                'error': 'patient_id and doctor_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            patient = Patient.objects.get(id=patient_id)
            doctor = Doctor.objects.get(id=doctor_id)
        except (Patient.DoesNotExist, Doctor.DoesNotExist):
            return Response({
                'error': 'Patient or doctor not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if assignment already exists
        existing = PatientDoctorAssignment.objects.filter(
            patient=patient, 
            doctor=doctor,
            is_active=True
        ).exists()
        
        if existing:
            return Response({
                'error': 'This patient is already assigned to this doctor'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create new assignment
        assignment = PatientDoctorAssignment.objects.create(
            patient=patient,
            doctor=doctor,
            notes=notes
        )
        
        serializer = PatientDoctorAssignmentSerializer(assignment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @swagger_auto_schema(
        method='get',
        operation_description="List all patient-doctor assignments",
        manual_parameters=[
            format_parameter,
            openapi.Parameter('doctor_id', openapi.IN_QUERY, type=openapi.TYPE_STRING, 
                            description="Filter by doctor ID"),
            openapi.Parameter('patient_id', openapi.IN_QUERY, type=openapi.TYPE_STRING, 
                            description="Filter by patient ID")
        ]
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def list_patient_doctor_assignments(self, request):
        """
        Endpoint for admin to list all patient-doctor assignments
        """
        assignments = PatientDoctorAssignment.objects.filter(is_active=True)
        
        # Optional filtering
        doctor_id = request.query_params.get('doctor_id')
        if doctor_id:
            assignments = assignments.filter(doctor_id=doctor_id)
            
        patient_id = request.query_params.get('patient_id')
        if patient_id:
            assignments = assignments.filter(patient_id=patient_id)
        
        serializer = PatientDoctorAssignmentSerializer(assignments, many=True, context={'request': request})
        
        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        if request.query_params.get('format') == 'fhir':
            response["Content-Type"] = "application/fhir+json"
            
        return response
    
    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def view_assignment(self, request, pk=None):
        """
        Endpoint for admin to view a specific patient-doctor assignment
        """
        assignment = get_object_or_404(PatientDoctorAssignment, pk=pk)
        serializer = PatientDoctorAssignmentSerializer(assignment)
        return Response(serializer.data)
