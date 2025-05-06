from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Doctor, Education
from .serializers import DoctorSerializer, EducationSerializer
from users.models import User, Role, Customer
from users.serializers import UserSerializer, CustomerSerializer
from django.shortcuts import get_object_or_404

class IsAdminUser(permissions.BasePermission):
    """
    Permission class to check if the user has admin role
    """
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False
        
        # Check if user has admin role
        return request.user.roles.filter(name='admin').exists()

class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAuthenticated]
    
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
        queryset = Doctor.objects.all()
        specialty = self.request.query_params.get('specialty')
        if specialty:
            queryset = queryset.filter(specialty__icontains=specialty)
        available = self.request.query_params.get('available')
        if available:
            queryset = queryset.filter(is_available=available.lower() == 'true')
        return queryset
        
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def admin_add_doctor(self, request):
        """
        Endpoint for admin to add a new doctor, creating both user and doctor profiles
        """
        # Create education record if provided
        education_data = request.data.get('education', {})
        education = None
        if education_data:
            education_serializer = EducationSerializer(data=education_data)
            if education_serializer.is_valid():
                education = education_serializer.save()
            else:
                return Response(education_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Create user account
        user_data = {
            'username': request.data.get('username'),
            'email': request.data.get('email'),
            'password': request.data.get('password'),
            'first_name': request.data.get('first_name'),
            'last_name': request.data.get('last_name'),
            'phone_number': request.data.get('phone_number', ''),
            'address': request.data.get('address', ''),
            'role_names': ['doctor']  # Assign doctor role
        }
        
        user_serializer = UserSerializer(data=user_data)
        if not user_serializer.is_valid():
            # Delete education if it was created
            if education:
                education.delete()
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = user_serializer.save()
        
        # Auto-verify the doctor account created by admin
        user.is_verified = True
        user.save()
        
        # Create doctor profile
        doctor_data = {
            'user_id': user.id,
            'specialty': request.data.get('specialty'),
            'license_number': request.data.get('license_number'),
            'experience_years': request.data.get('experience_years', 0),
            'bio': request.data.get('bio', ''),
            'education': education.id if education else None,
            'is_verified': True,  # Auto-verify doctor profiles created by admin
            'is_available': request.data.get('is_available', True)
        }
        
        doctor_serializer = self.get_serializer(data=doctor_data)
        if not doctor_serializer.is_valid():
            # Delete user and education if doctor creation fails
            user.delete()
            if education:
                education.delete()
            return Response(doctor_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        doctor = doctor_serializer.save()
        
        return Response({
            'doctor': doctor_serializer.data,
            'user': user_serializer.data,
            'message': 'Doctor account created successfully by admin'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def admin_list_doctors(self, request):
        """
        Endpoint for admin to view all doctors
        """
        # Get all doctors
        doctors = Doctor.objects.all()
        
        # Serialize the data
        serializer = self.get_serializer(doctors, many=True)
        
        return Response(serializer.data)
        
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def admin_list_patients(self, request):
        """
        Endpoint for admin to view all patients
        """
        # Get patient role
        patient_role = get_object_or_404(Role, name='patient')
        
        # Get all users with patient role
        patients = Customer.objects.filter(user__roles=patient_role)
        
        # Serialize the data
        serializer = CustomerSerializer(patients, many=True)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def admin_view_doctor(self, request, pk=None):
        """
        Endpoint for admin to view a specific doctor
        """
        doctor = get_object_or_404(Doctor, pk=pk)
        serializer = self.get_serializer(doctor)
        return Response(serializer.data)
        
    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def admin_view_patient(self, request, pk=None):
        """
        Endpoint for admin to view a specific patient
        """
        patient = get_object_or_404(Customer, pk=pk)
        serializer = CustomerSerializer(patient)
        return Response(serializer.data)
