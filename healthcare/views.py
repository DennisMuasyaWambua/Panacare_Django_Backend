from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import HealthCare, PatientDoctorAssignment
from .serializers import HealthCareSerializer, PatientDoctorAssignmentSerializer
from doctors.views import IsAdminUser
from users.models import User, Role, Customer
from doctors.models import Doctor
from django.shortcuts import get_object_or_404

class HealthCareViewSet(viewsets.ModelViewSet):
    queryset = HealthCare.objects.all()
    serializer_class = HealthCareSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def finalize_response(self, request, response, *args, **kwargs):
        """
        Add CORS headers to all responses
        """
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-Requested-With"
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
            patient = Customer.objects.get(id=patient_id)
            doctor = Doctor.objects.get(id=doctor_id)
        except (Customer.DoesNotExist, Doctor.DoesNotExist):
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
        
        serializer = PatientDoctorAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def view_assignment(self, request, pk=None):
        """
        Endpoint for admin to view a specific patient-doctor assignment
        """
        assignment = get_object_or_404(PatientDoctorAssignment, pk=pk)
        serializer = PatientDoctorAssignmentSerializer(assignment)
        return Response(serializer.data)
