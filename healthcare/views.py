from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.db.models import Q, Avg
from datetime import datetime, timedelta
from .models import (
    HealthCare, PatientDoctorAssignment, DoctorAvailability, 
    Appointment, AppointmentDocument, Consultation, 
    Package, PatientSubscription, Resource, DoctorRating
)
from .serializers import (
    HealthCareSerializer, PatientDoctorAssignmentSerializer,
    DoctorAvailabilitySerializer, AppointmentSerializer,
    AppointmentDocumentSerializer, ConsultationSerializer,
    PackageSerializer, PatientSubscriptionSerializer,
    ResourceSerializer, DoctorRatingSerializer
)
from doctors.views import IsAdminUser, IsVerifiedUser
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


class IsPatientUser(permissions.BasePermission):
    """
    Permission class to check if the user has patient role
    """
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False
        
        # Check if user has patient role
        return request.user.roles.filter(name='patient').exists()


class IsDoctorUser(permissions.BasePermission):
    """
    Permission class to check if the user has doctor role
    """
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False
        
        # Check if user has doctor role
        return request.user.roles.filter(name='doctor').exists()


class IsPatientOrDoctorOrAdmin(permissions.BasePermission):
    """
    Permission class to check if the user has patient, doctor or admin role
    """
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False
        
        # Check if user has patient, doctor or admin role
        return request.user.roles.filter(name__in=['patient', 'doctor', 'admin']).exists()


class DoctorAvailabilityViewSet(viewsets.ModelViewSet):
    queryset = DoctorAvailability.objects.all()
    serializer_class = DoctorAvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """
        Override to set custom permissions for different actions
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsDoctorUser | IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = DoctorAvailability.objects.all()
        
        # Optional filtering
        doctor_id = self.request.query_params.get('doctor_id')
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
            
        is_available = self.request.query_params.get('available')
        if is_available:
            queryset = queryset.filter(is_available=is_available.lower() == 'true')
            
        day_of_week = self.request.query_params.get('day')
        if day_of_week:
            try:
                day_of_week = int(day_of_week)
                queryset = queryset.filter(day_of_week=day_of_week)
            except ValueError:
                pass
                
        date = self.request.query_params.get('date')
        if date:
            try:
                specific_date = datetime.strptime(date, '%Y-%m-%d').date()
                queryset = queryset.filter(
                    Q(specific_date=specific_date) | 
                    (Q(is_recurring=True) & Q(day_of_week=specific_date.weekday()))
                )
            except ValueError:
                pass
                
        return queryset
    
    @action(detail=False, methods=['get'], permission_classes=[IsDoctorUser])
    def my_availability(self, request):
        """
        Endpoint for doctors to view their own availability
        """
        try:
            doctor = request.user.doctor
            availabilities = DoctorAvailability.objects.filter(doctor=doctor)
            serializer = self.get_serializer(availabilities, many=True)
            return Response(serializer.data)
        except Doctor.DoesNotExist:
            return Response({
                'error': 'Doctor profile not found'
            }, status=status.HTTP_404_NOT_FOUND)


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """
        Override to set custom permissions for different actions
        """
        if self.action in ['create']:
            permission_classes = [IsPatientUser | IsAdminUser]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsPatientOrDoctorOrAdmin]
        elif self.action in ['destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = Appointment.objects.all()
        
        # Filter by role
        if self.request.user.roles.filter(name='admin').exists():
            # Admin can see all appointments
            pass
        elif self.request.user.roles.filter(name='doctor').exists():
            # Doctors can only see their own appointments
            try:
                doctor = self.request.user.doctor
                queryset = queryset.filter(doctor=doctor)
            except Doctor.DoesNotExist:
                return Appointment.objects.none()
        elif self.request.user.roles.filter(name='patient').exists():
            # Patients can only see their own appointments
            try:
                patient = self.request.user.patient
                queryset = queryset.filter(patient=patient)
            except Patient.DoesNotExist:
                return Appointment.objects.none()
        else:
            return Appointment.objects.none()
            
        # Optional filtering
        doctor_id = self.request.query_params.get('doctor_id')
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
            
        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
            
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
            
        date_from = self.request.query_params.get('date_from')
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(appointment_date__gte=date_from)
            except ValueError:
                pass
                
        date_to = self.request.query_params.get('date_to')
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(appointment_date__lte=date_to)
            except ValueError:
                pass
                
        appointment_type = self.request.query_params.get('type')
        if appointment_type:
            queryset = queryset.filter(appointment_type=appointment_type)
                
        return queryset
    
    @action(detail=False, methods=['get'], permission_classes=[IsPatientUser])
    def my_appointments(self, request):
        """
        Endpoint for patients to view their own appointments
        """
        try:
            patient = request.user.patient
            appointments = Appointment.objects.filter(patient=patient)
            
            # Optional filtering
            status_param = request.query_params.get('status')
            if status_param:
                appointments = appointments.filter(status=status_param)
                
            date_from = request.query_params.get('date_from')
            if date_from:
                try:
                    date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                    appointments = appointments.filter(appointment_date__gte=date_from)
                except ValueError:
                    pass
                    
            date_to = request.query_params.get('date_to')
            if date_to:
                try:
                    date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                    appointments = appointments.filter(appointment_date__lte=date_to)
                except ValueError:
                    pass
                    
            doctor_id = request.query_params.get('doctor_id')
            if doctor_id:
                appointments = appointments.filter(doctor_id=doctor_id)
                
            serializer = self.get_serializer(appointments, many=True)
            return Response(serializer.data)
        except Patient.DoesNotExist:
            return Response({
                'error': 'Patient profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'], permission_classes=[IsDoctorUser])
    def doctor_appointments(self, request):
        """
        Endpoint for doctors to view their own appointments
        """
        try:
            doctor = request.user.doctor
            appointments = Appointment.objects.filter(doctor=doctor)
            
            # Optional filtering
            status_param = request.query_params.get('status')
            if status_param:
                appointments = appointments.filter(status=status_param)
                
            date_from = request.query_params.get('date_from')
            if date_from:
                try:
                    date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                    appointments = appointments.filter(appointment_date__gte=date_from)
                except ValueError:
                    pass
                    
            date_to = request.query_params.get('date_to')
            if date_to:
                try:
                    date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                    appointments = appointments.filter(appointment_date__lte=date_to)
                except ValueError:
                    pass
                    
            patient_id = request.query_params.get('patient_id')
            if patient_id:
                appointments = appointments.filter(patient_id=patient_id)
                
            serializer = self.get_serializer(appointments, many=True)
            return Response(serializer.data)
        except Doctor.DoesNotExist:
            return Response({
                'error': 'Doctor profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
            
    @action(detail=True, methods=['post'], permission_classes=[IsPatientUser])
    def cancel_appointment(self, request, pk=None):
        """
        Endpoint for patients to cancel their appointments
        """
        appointment = self.get_object()
        
        # Check if patient owns this appointment
        if not appointment.patient.user == request.user:
            return Response({
                'error': 'You can only cancel your own appointments'
            }, status=status.HTTP_403_FORBIDDEN)
            
        # Check if appointment can be cancelled
        if appointment.status in ['fulfilled', 'cancelled', 'noshow']:
            return Response({
                'error': f'Cannot cancel an appointment with status: {appointment.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Cancel the appointment
        appointment.status = 'cancelled'
        appointment.save()
        
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsDoctorUser])
    def update_consultation_details(self, request, pk=None):
        """
        Endpoint for doctors to update consultation details (diagnosis, treatment, etc.)
        """
        appointment = self.get_object()
        
        # Check if doctor owns this appointment
        if not appointment.doctor.user == request.user:
            return Response({
                'error': 'You can only update your own appointments'
            }, status=status.HTTP_403_FORBIDDEN)
            
        # Update the appointment
        diagnosis = request.data.get('diagnosis')
        if diagnosis is not None:
            appointment.diagnosis = diagnosis
            
        treatment = request.data.get('treatment')
        if treatment is not None:
            appointment.treatment = treatment
            
        notes = request.data.get('notes')
        if notes is not None:
            appointment.notes = notes
            
        risk_level = request.data.get('risk_level')
        if risk_level is not None:
            appointment.risk_level = risk_level
            
        # Change status to fulfilled if requested
        status_param = request.data.get('status')
        if status_param:
            appointment.status = status_param
            
        appointment.save()
        
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)


class AppointmentDocumentViewSet(viewsets.ModelViewSet):
    queryset = AppointmentDocument.objects.all()
    serializer_class = AppointmentDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [IsDoctorUser | IsAdminUser]
        elif self.action in ['destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsPatientOrDoctorOrAdmin]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = AppointmentDocument.objects.all()
        
        # Filter by role
        if self.request.user.roles.filter(name='admin').exists():
            # Admin can see all documents
            pass
        elif self.request.user.roles.filter(name='doctor').exists():
            # Doctors can only see documents for their appointments
            try:
                doctor = self.request.user.doctor
                queryset = queryset.filter(appointment__doctor=doctor)
            except Doctor.DoesNotExist:
                return AppointmentDocument.objects.none()
        elif self.request.user.roles.filter(name='patient').exists():
            # Patients can only see their own documents
            try:
                patient = self.request.user.patient
                queryset = queryset.filter(appointment__patient=patient)
            except Patient.DoesNotExist:
                return AppointmentDocument.objects.none()
        else:
            return AppointmentDocument.objects.none()
            
        # Optional filtering
        appointment_id = self.request.query_params.get('appointment_id')
        if appointment_id:
            queryset = queryset.filter(appointment_id=appointment_id)
            
        document_type = self.request.query_params.get('type')
        if document_type:
            queryset = queryset.filter(document_type=document_type)
                
        return queryset
    
    def perform_create(self, serializer):
        # Set uploaded_by to current user
        serializer.save(uploaded_by=self.request.user)


class ConsultationViewSet(viewsets.ModelViewSet):
    queryset = Consultation.objects.all()
    serializer_class = ConsultationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [IsDoctorUser | IsAdminUser]
        elif self.action in ['destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsPatientOrDoctorOrAdmin]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = Consultation.objects.all()
        
        # Filter by role
        if self.request.user.roles.filter(name='admin').exists():
            # Admin can see all consultations
            pass
        elif self.request.user.roles.filter(name='doctor').exists():
            # Doctors can only see their own consultations
            try:
                doctor = self.request.user.doctor
                queryset = queryset.filter(appointment__doctor=doctor)
            except Doctor.DoesNotExist:
                return Consultation.objects.none()
        elif self.request.user.roles.filter(name='patient').exists():
            # Patients can only see their own consultations
            try:
                patient = self.request.user.patient
                queryset = queryset.filter(appointment__patient=patient)
            except Patient.DoesNotExist:
                return Consultation.objects.none()
        else:
            return Consultation.objects.none()
            
        # Optional filtering
        appointment_id = self.request.query_params.get('appointment_id')
        if appointment_id:
            queryset = queryset.filter(appointment_id=appointment_id)
            
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
                
        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[IsDoctorUser])
    def start_consultation(self, request, pk=None):
        """
        Endpoint for doctors to start a consultation
        """
        consultation = self.get_object()
        
        # Check if doctor owns this consultation
        if not consultation.appointment.doctor.user == request.user:
            return Response({
                'error': 'You can only start your own consultations'
            }, status=status.HTTP_403_FORBIDDEN)
            
        # Check if consultation can be started
        if consultation.status not in ['scheduled']:
            return Response({
                'error': f'Cannot start a consultation with status: {consultation.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Start the consultation
        consultation.status = 'in-progress'
        consultation.start_time = timezone.now()
        consultation.save()
        
        # Update appointment status
        appointment = consultation.appointment
        appointment.status = 'arrived'
        appointment.save()
        
        serializer = self.get_serializer(consultation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsDoctorUser])
    def end_consultation(self, request, pk=None):
        """
        Endpoint for doctors to end a consultation
        """
        consultation = self.get_object()
        
        # Check if doctor owns this consultation
        if not consultation.appointment.doctor.user == request.user:
            return Response({
                'error': 'You can only end your own consultations'
            }, status=status.HTTP_403_FORBIDDEN)
            
        # Check if consultation can be ended
        if consultation.status not in ['in-progress']:
            return Response({
                'error': f'Cannot end a consultation with status: {consultation.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # End the consultation
        consultation.status = 'completed'
        consultation.end_time = timezone.now()
        consultation.save()
        
        # Update appointment status
        appointment = consultation.appointment
        appointment.status = 'fulfilled'
        appointment.save()
        
        serializer = self.get_serializer(consultation)
        return Response(serializer.data)


class PackageViewSet(viewsets.ModelViewSet):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = Package.objects.filter(is_active=True)
        
        # Admin can see inactive packages too with a filter
        if self.request.user.roles.filter(name='admin').exists():
            include_inactive = self.request.query_params.get('include_inactive')
            if include_inactive and include_inactive.lower() == 'true':
                queryset = Package.objects.all()
                
        return queryset


class PatientSubscriptionViewSet(viewsets.ModelViewSet):
    queryset = PatientSubscription.objects.all()
    serializer_class = PatientSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [IsPatientUser | IsAdminUser]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = PatientSubscription.objects.all()
        
        # Filter by role
        if self.request.user.roles.filter(name='admin').exists():
            # Admin can see all subscriptions
            pass
        elif self.request.user.roles.filter(name='patient').exists():
            # Patients can only see their own subscriptions
            try:
                patient = self.request.user.patient
                queryset = queryset.filter(patient=patient)
            except Patient.DoesNotExist:
                return PatientSubscription.objects.none()
        else:
            return PatientSubscription.objects.none()
            
        # Optional filtering
        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
            
        package_id = self.request.query_params.get('package_id')
        if package_id:
            queryset = queryset.filter(package_id=package_id)
            
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
                
        return queryset
    
    @action(detail=False, methods=['get'], permission_classes=[IsPatientUser])
    def my_subscriptions(self, request):
        """
        Endpoint for patients to view their own subscriptions
        """
        try:
            patient = request.user.patient
            subscriptions = PatientSubscription.objects.filter(patient=patient)
            
            # Optional filtering
            status_param = request.query_params.get('status')
            if status_param:
                subscriptions = subscriptions.filter(status=status_param)
                
            serializer = self.get_serializer(subscriptions, many=True)
            return Response(serializer.data)
        except Patient.DoesNotExist:
            return Response({
                'error': 'Patient profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'], permission_classes=[IsPatientUser])
    def cancel_subscription(self, request, pk=None):
        """
        Endpoint for patients to cancel their subscription
        """
        subscription = self.get_object()
        
        # Check if patient owns this subscription
        if not subscription.patient.user == request.user:
            return Response({
                'error': 'You can only cancel your own subscriptions'
            }, status=status.HTTP_403_FORBIDDEN)
            
        # Check if subscription can be cancelled
        if subscription.status not in ['active']:
            return Response({
                'error': f'Cannot cancel a subscription with status: {subscription.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Cancel the subscription
        subscription.status = 'cancelled'
        subscription.save()
        
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)


class ResourceViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [IsDoctorUser | IsAdminUser]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = Resource.objects.filter(is_active=True, is_approved=True)
        
        # Admin can see all resources
        if self.request.user.roles.filter(name='admin').exists():
            include_unapproved = self.request.query_params.get('include_unapproved')
            if include_unapproved and include_unapproved.lower() == 'true':
                queryset = Resource.objects.all()
        
        # Doctors can see their own unapproved resources
        elif self.request.user.roles.filter(name='doctor').exists():
            try:
                doctor = self.request.user.doctor
                include_unapproved = self.request.query_params.get('include_unapproved')
                if include_unapproved and include_unapproved.lower() == 'true':
                    queryset = queryset.filter(Q(is_approved=True) | Q(author=doctor))
            except Doctor.DoesNotExist:
                pass
                
        # Optional filtering
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
            
        content_type = self.request.query_params.get('content_type')
        if content_type:
            queryset = queryset.filter(content_type=content_type)
            
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) |
                Q(tags__icontains=search)
            )
                
        return queryset
    
    def perform_create(self, serializer):
        # Set author to doctor if user is a doctor
        if self.request.user.roles.filter(name='doctor').exists():
            try:
                doctor = self.request.user.doctor
                serializer.save(author=doctor, is_approved=False)
            except Doctor.DoesNotExist:
                serializer.save(is_approved=False)
        else:
            # Admin uploads are auto-approved
            serializer.save(is_approved=True, approved_by=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve_resource(self, request, pk=None):
        """
        Endpoint for admins to approve a resource
        """
        resource = self.get_object()
        
        # Check if resource is already approved
        if resource.is_approved:
            return Response({
                'error': 'Resource is already approved'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Approve the resource
        resource.is_approved = True
        resource.approved_by = request.user
        resource.save()
        
        serializer = self.get_serializer(resource)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def verify_password(self, request, pk=None):
        """
        Endpoint to verify password for password-protected resources
        """
        resource = self.get_object()
        
        # Check if resource is password-protected
        if not resource.is_password_protected:
            return Response({
                'error': 'This resource is not password-protected'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Verify password
        from django.contrib.auth.hashers import check_password
        password = request.data.get('password')
        if password and check_password(password, resource.password_hash):
            return Response({
                'message': 'Password verified',
                'resource': self.get_serializer(resource).data
            })
        else:
            return Response({
                'error': 'Invalid password'
            }, status=status.HTTP_401_UNAUTHORIZED)


class DoctorRatingViewSet(viewsets.ModelViewSet):
    queryset = DoctorRating.objects.all()
    serializer_class = DoctorRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [IsPatientUser]
        elif self.action in ['destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = DoctorRating.objects.all()
        
        # Optional filtering
        doctor_id = self.request.query_params.get('doctor_id')
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
            
        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
            
        rating = self.request.query_params.get('rating')
        if rating:
            try:
                rating = int(rating)
                queryset = queryset.filter(rating=rating)
            except ValueError:
                pass
                
        return queryset
    
    def perform_create(self, serializer):
        try:
            # Set patient to current user's patient
            patient = self.request.user.patient
            
            # Check if patient has already rated this doctor
            doctor_id = serializer.validated_data.get('doctor').id
            existing_rating = DoctorRating.objects.filter(doctor_id=doctor_id, patient=patient).exists()
            
            if existing_rating:
                # Update the existing rating
                existing_rating = DoctorRating.objects.get(doctor_id=doctor_id, patient=patient)
                existing_rating.rating = serializer.validated_data.get('rating')
                existing_rating.review = serializer.validated_data.get('review', '')
                existing_rating.is_anonymous = serializer.validated_data.get('is_anonymous', False)
                existing_rating.save()
            else:
                # Create new rating
                serializer.save(patient=patient)
        except Patient.DoesNotExist:
            raise serializers.ValidationError("Patient profile not found")
    
    @action(detail=False, methods=['get'])
    def doctor_average_rating(self, request):
        """
        Get the average rating for a doctor
        """
        doctor_id = request.query_params.get('doctor_id')
        if not doctor_id:
            return Response({
                'error': 'doctor_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Get average rating
        average_rating = DoctorRating.objects.filter(doctor_id=doctor_id).aggregate(Avg('rating'))
        total_ratings = DoctorRating.objects.filter(doctor_id=doctor_id).count()
        
        return Response({
            'doctor_id': doctor_id,
            'average_rating': average_rating['rating__avg'] or 0,
            'total_ratings': total_ratings
        })
