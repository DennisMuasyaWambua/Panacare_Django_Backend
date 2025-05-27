from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from .models import Doctor, Education
from .serializers import DoctorSerializer, EducationSerializer
from users.models import User, Role, Patient
from users.serializers import UserSerializer, PatientSerializer
from django.shortcuts import get_object_or_404
from django.db import models
from django.db.models import Avg, Count
from healthcare.models import DoctorRating
from healthcare.serializers import DoctorRatingSerializer

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

class IsVerifiedUser(permissions.BasePermission):
    """
    Permission class to check if the user is verified
    """
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False
        
        # Check if user is verified
        return request.user.is_verified

class IsPatientUser(permissions.BasePermission):
    """
    Permission class to check if the user has patient role
    """
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False
        
        # Check if user has patient role
        return request.user.roles.filter(name='patient').exists() and hasattr(request.user, 'patient')
        
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

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsVerifiedUser])
def add_doctor_profile(request):
    """
    Dedicated endpoint for verified users to add their own doctor profile
    This is separate from the admin pathway and specifically for doctors after registration and verification
    """
    # Check if user has a doctor role
    if not request.user.roles.filter(name='doctor').exists():
        return Response(
            {"error": "Only users with doctor role can create a doctor profile"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if doctor profile already exists for this user
    if hasattr(request.user, 'doctor'):
        return Response(
            {"error": "Doctor profile already exists for this user"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create education record if provided
    education_data = request.data.get('education', {})
    education = None
    if education_data:
        education_serializer = EducationSerializer(data=education_data)
        if education_serializer.is_valid():
            education = education_serializer.save()
        else:
            return Response(education_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        # Education is required, so create a default one if not provided
        default_education = {
            'level_of_education': 'Not Specified',
            'field': 'Medicine',
            'institution': 'Not Specified'
        }
        education_serializer = EducationSerializer(data=default_education)
        if education_serializer.is_valid():
            education = education_serializer.save()
        else:
            return Response(education_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Create doctor profile with current user ID
    doctor_data = {
        'user_id': request.user.id,
        'specialty': request.data.get('specialty', 'General Practice'),
        'license_number': request.data.get('license_number', 'Pending'),
        'experience_years': request.data.get('experience_years', 0),
        'bio': request.data.get('bio', ''),
        'education': education.id,
        'is_verified': False,  # Admin will need to verify doctor profiles
        'is_available': request.data.get('is_available', True),
        'communication_languages': request.data.get('communication_languages', 'en')
    }
    
    doctor_serializer = DoctorSerializer(data=doctor_data)
    if not doctor_serializer.is_valid():
        # Delete education if it was created but doctor profile creation fails
        if education:
            education.delete()
        return Response(doctor_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    doctor = doctor_serializer.save()
    
    return Response({
        'doctor': doctor_serializer.data,
        'message': 'Doctor profile created successfully. An admin will review and verify your profile.'
    }, status=status.HTTP_201_CREATED)

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

class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="List all doctors. Patients can use this endpoint to see available doctors and filter them.",
        manual_parameters=[
            format_parameter,
            openapi.Parameter('specialty', openapi.IN_QUERY, type=openapi.TYPE_STRING, description="Filter by specialty"),
            openapi.Parameter('available', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, description="Filter by availability"),
            openapi.Parameter('name', openapi.IN_QUERY, type=openapi.TYPE_STRING, description="Filter by doctor's first or last name"),
            openapi.Parameter('location', openapi.IN_QUERY, type=openapi.TYPE_STRING, description="Filter by doctor's location/address")
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
        
    @swagger_auto_schema(
        operation_description="Get details of a specific doctor",
        manual_parameters=[format_parameter]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    def initial(self, request, *args, **kwargs):
        """
        Add CORS headers to all responses
        """
        super().initial(request, *args, **kwargs)
    
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
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        elif self.action == 'create':
            # For create, allow either admin users or verified users with doctor role
            permission_classes = [IsAdminUser | IsVerifiedUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = Doctor.objects.all()
        
        # Filter by specialty
        specialty = self.request.query_params.get('specialty')
        if specialty:
            queryset = queryset.filter(specialty__icontains=specialty)
            
        # Filter by availability
        available = self.request.query_params.get('available')
        if available:
            queryset = queryset.filter(is_available=available.lower() == 'true')
            
        # Filter by doctor name (first or last name)
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(
                models.Q(user__first_name__icontains=name) | 
                models.Q(user__last_name__icontains=name)
            )
            
        # Filter by location (address)
        location = self.request.query_params.get('location')
        if location:
            queryset = queryset.filter(user__address__icontains=location)
            
        return queryset
        
    def create(self, request, *args, **kwargs):
        # For verified users creating their own doctor profile
        if not request.user.roles.filter(name='admin').exists():
            # If this is a regular user (not admin), we need to make some checks
            # and override the user_id with the current user's ID for security
            
            # Check if user has a doctor role
            if not request.user.roles.filter(name='doctor').exists():
                return Response(
                    {"error": "Only users with doctor role can create a doctor profile"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if doctor profile already exists for this user
            if hasattr(request.user, 'doctor'):
                return Response(
                    {"error": "Doctor profile already exists for this user"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Override the user_id in the request data with the current user's ID
            request.data['user_id'] = request.user.id
            
            # Create education record if provided
            education_data = request.data.get('education', {})
            education = None
            if education_data:
                education_serializer = EducationSerializer(data=education_data)
                if education_serializer.is_valid():
                    education = education_serializer.save()
                    request.data['education'] = education.id
                else:
                    return Response(education_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Education is required, so create a default one if not provided
                default_education = {
                    'level_of_education': 'Not Specified',
                    'field': 'Medicine',
                    'institution': 'Not Specified'
                }
                education_serializer = EducationSerializer(data=default_education)
                if education_serializer.is_valid():
                    education = education_serializer.save()
                    request.data['education'] = education.id
                else:
                    return Response(education_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
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
        # Log the request user for debugging
        print(f"Admin list doctors requested by: {request.user.email}")
        
        # Get all doctors
        doctors = Doctor.objects.all()
        
        # Log the count of doctors
        print(f"Total doctors found: {doctors.count()}")
        for doctor in doctors:
            print(f"Doctor: {doctor.id} - {doctor.user.get_full_name()} - Verified: {doctor.is_verified}")
        
        # Check for users with doctor role but no doctor profile
        doctor_role = Role.objects.filter(name='doctor').first()
        if doctor_role:
            users_with_doctor_role = User.objects.filter(roles=doctor_role)
            print(f"Users with doctor role: {users_with_doctor_role.count()}")
            
            # Find users with doctor role but no doctor profile
            missing_profiles = []
            for user in users_with_doctor_role:
                if not hasattr(user, 'doctor'):
                    missing_profiles.append(f"{user.id} - {user.get_full_name()}")
            
            if missing_profiles:
                print(f"Users with doctor role but no doctor profile: {len(missing_profiles)}")
                for profile in missing_profiles:
                    print(f"Missing profile: {profile}")
        
        # Get verification status filter if provided
        is_verified = request.query_params.get('is_verified')
        if is_verified is not None:
            is_verified_bool = is_verified.lower() == 'true'
            doctors = doctors.filter(is_verified=is_verified_bool)
            print(f"Filtered to {doctors.count()} doctors with is_verified={is_verified_bool}")
        
        # Serialize the data
        serializer = self.get_serializer(doctors, many=True)
        
        # Add CORS headers to the response
        response = Response(serializer.data)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        
        return response
        
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def admin_list_patients(self, request):
        """
        Endpoint for admin to view all patients
        """
        # Get patient role
        patient_role = get_object_or_404(Role, name='patient')
        
        # Get all users with patient role
        patients = Patient.objects.filter(user__roles=patient_role)
        
        # Serialize the data
        serializer = PatientSerializer(patients, many=True, context={'request': request})
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def admin_view_doctor(self, request, pk=None):
        """
        Endpoint for admin to view a specific doctor
        """
        doctor = get_object_or_404(Doctor, pk=pk)
        serializer = self.get_serializer(doctor)
        return Response(serializer.data)
        
    @action(detail=True, methods=['patch'], permission_classes=[IsAdminUser])
    def verify_doctor(self, request, pk=None):
        """
        Endpoint for admin to verify a doctor's profile
        """
        try:
            # First try to get doctor by primary key
            doctor = Doctor.objects.get(pk=pk)
        except Doctor.DoesNotExist:
            # Log the attempted pk for debugging
            print(f"Failed to find doctor with pk: {pk}")
            
            # Try to find by user ID as fallback (in case the ID is a user ID)
            try:
                user = User.objects.get(pk=pk)
                if hasattr(user, 'doctor'):
                    doctor = user.doctor
                else:
                    return Response({
                        'error': f"Found user with ID {pk} but they don't have a doctor profile"
                    }, status=status.HTTP_404_NOT_FOUND)
            except User.DoesNotExist:
                return Response({
                    'error': f"No Doctor or User found with ID: {pk}"
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Get verification status from request data
        is_verified = request.data.get('is_verified', True)
        
        # Update verification status
        doctor.is_verified = is_verified
        doctor.save()
        
        serializer = self.get_serializer(doctor)
        return Response({
            'message': f"Doctor verification status updated to: {is_verified}",
            'doctor': serializer.data
        }, status=status.HTTP_200_OK)
        
    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def admin_view_patient(self, request, pk=None):
        """
        Endpoint for admin to view a specific patient
        """
        patient = get_object_or_404(Patient, pk=pk)
        serializer = PatientSerializer(patient, context={'request': request})
        return Response(serializer.data)
        
    @swagger_auto_schema(
        operation_description="Get doctor's own profile",
        manual_parameters=[format_parameter]
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def profile(self, request):
        """
        Endpoint for doctors to view their own profile
        """
        # Check if user has doctor role
        if not request.user.roles.filter(name='doctor').exists():
            return Response({
                'error': 'Only doctors can access this endpoint'
            }, status=status.HTTP_403_FORBIDDEN)
            
        try:
            doctor = Doctor.objects.get(user=request.user)
            serializer = self.get_serializer(doctor, context={'request': request})
            
            # Set appropriate content type for FHIR responses
            response = Response(serializer.data)
            if request.query_params.get('format') == 'fhir':
                response["Content-Type"] = "application/fhir+json"
            
            return response
        except Doctor.DoesNotExist:
            return Response({
                'error': 'Doctor profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_description="Get ratings for a specific doctor"
    )
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def ratings(self, request, pk=None):
        """
        Endpoint for viewing all ratings for a specific doctor.
        Accessible by any authenticated user.
        """
        doctor = self.get_object()
        ratings = DoctorRating.objects.filter(doctor=doctor)
        
        # Apply pagination
        page = self.paginate_queryset(ratings)
        if page is not None:
            serializer = DoctorRatingSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = DoctorRatingSerializer(ratings, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Get summary of ratings for a specific doctor"
    )
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def rating_summary(self, request, pk=None):
        """
        Endpoint for viewing summary statistics of ratings for a specific doctor.
        Accessible by any authenticated user.
        """
        doctor = self.get_object()
        
        # Get ratings data
        ratings = DoctorRating.objects.filter(doctor=doctor)
        total_ratings = ratings.count()
        
        if total_ratings == 0:
            return Response({
                'doctor_id': str(doctor.id),
                'doctor_name': doctor.user.get_full_name(),
                'average_rating': 0,
                'total_ratings': 0,
                'rating_distribution': {
                    '1': 0, '2': 0, '3': 0, '4': 0, '5': 0
                }
            })
        
        # Calculate average
        avg_rating = ratings.aggregate(Avg('rating'))['rating__avg']
        
        # Calculate distribution
        distribution = ratings.values('rating').annotate(count=Count('rating')).order_by('rating')
        rating_distribution = {str(i): 0 for i in range(1, 6)}
        for item in distribution:
            rating_distribution[str(item['rating'])] = item['count']
        
        return Response({
            'doctor_id': str(doctor.id),
            'doctor_name': doctor.user.get_full_name(),
            'average_rating': avg_rating,
            'total_ratings': total_ratings,
            'rating_distribution': rating_distribution
        })
        
    @swagger_auto_schema(
        operation_description="Create a review for a doctor",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['rating'],
            properties={
                'rating': openapi.Schema(type=openapi.TYPE_INTEGER, description="Rating (1-5 stars)", minimum=1, maximum=5),
                'review': openapi.Schema(type=openapi.TYPE_STRING, description="Text review"),
                'is_anonymous': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Whether to post review anonymously")
            }
        )
    )
    @action(detail=True, methods=['post'], permission_classes=[IsPatientUser])
    def review(self, request, pk=None):
        """
        Endpoint for patients to create a review for a doctor.
        Only accessible by authenticated users with patient role.
        """
        doctor = self.get_object()
        
        # Validate input data
        rating = request.data.get('rating')
        if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
            return Response({
                'error': 'Rating must be an integer between 1 and 5'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        review_text = request.data.get('review', '')
        is_anonymous = request.data.get('is_anonymous', False)
        
        try:
            patient = request.user.patient
            
            # Check if patient has already rated this doctor
            existing_rating = DoctorRating.objects.filter(doctor=doctor, patient=patient).first()
            
            if existing_rating:
                # Update existing rating
                existing_rating.rating = rating
                existing_rating.review = review_text
                existing_rating.is_anonymous = is_anonymous
                existing_rating.save()
                message = "Review updated successfully"
            else:
                # Create new rating
                DoctorRating.objects.create(
                    doctor=doctor,
                    patient=patient,
                    rating=rating,
                    review=review_text,
                    is_anonymous=is_anonymous
                )
                message = "Review created successfully"
            
            return Response({
                'message': message,
                'doctor_id': str(doctor.id),
                'doctor_name': doctor.user.get_full_name()
            }, status=status.HTTP_201_CREATED)
            
        except Patient.DoesNotExist:
            return Response({
                'error': 'Patient profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
