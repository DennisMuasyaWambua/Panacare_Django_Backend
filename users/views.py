import os
import logging
import datetime
import secrets
import hashlib
import csv
from io import StringIO
from rest_framework import status, permissions, viewsets, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.decorators import api_view, permission_classes, action
from django.contrib.auth import authenticate, update_session_auth_hash
from django.shortcuts import get_object_or_404
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.db import models
from django.db.models import Q
from django.http import HttpResponse
from rest_framework_simplejwt.tokens import RefreshToken
from panacare.settings import SIMPLE_JWT
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django_filters.rest_framework import DjangoFilterBackend
# Temporarily comment out google.fhir imports to allow migrations
# from google.fhir.r4 import json_format
# from google.fhir.r4.proto.core.resources import patient_pb2
# from google.fhir.r4.proto.core import codes_pb2, datatypes_pb2
import json

from .models import User, Role, Patient, AuditLog, Location, CommunityHealthProvider, CHPPatientMessage
from .serializers import (
    UserSerializer, RoleSerializer, PatientSerializer, 
    PasswordChangeSerializer, EmailChangeSerializer, PhoneChangeSerializer,
    ContactUsSerializer, SupportRequestSerializer, ForgotPasswordSerializer,
    AuditLogSerializer, AuditLogFilterSerializer, CommunityHealthProviderSerializer,
    CHPPatientCreateSerializer, CHPPatientMessageSerializer, CHPAssignmentSerializer
)
from .locations import LocationService
from doctors.models import Doctor
from doctors.serializers import DoctorSerializer
from healthcare.models import Referral
from healthcare.serializers import ReferralCreateSerializer, ReferralListSerializer, ReferralDetailSerializer

# Generate a secure token for admin registration
# This is a one-time use token that should be removed after use
ADMIN_REGISTRATION_TOKEN = "panacare_secure_admin_token_2025"
# Create a hash of the token for comparison (more secure than plain text)
ADMIN_TOKEN_HASH = hashlib.sha256(ADMIN_REGISTRATION_TOKEN.encode()).hexdigest()

logger = logging.getLogger(__name__)

def create_fhir_patient(patient):
    """
    Create a FHIR Patient resource using google-fhir-r4 library
    """
    fhir_patient = patient_pb2.Patient()
    fhir_patient.id.value = str(patient.id)
    fhir_patient.active.value = patient.active
    
    identifier = fhir_patient.identifier.add()
    identifier.system.value = patient.identifier_system or "urn:panacare:patient"
    identifier.value.value = str(patient.id)
    
    name = fhir_patient.name.add()
    name.use.value = codes_pb2.NameUseCode.OFFICIAL
    name.family.value = patient.user.last_name if patient.user.last_name else ""
    if patient.user.first_name:
        given = name.given.add()
        given.value = patient.user.first_name
    
    if patient.user.email:
        email_telecom = fhir_patient.telecom.add()
        email_telecom.system.value = codes_pb2.ContactPointSystemCode.EMAIL
        email_telecom.value.value = patient.user.email
        email_telecom.use.value = codes_pb2.ContactPointUseCode.HOME
    
    if patient.user.phone_number:
        phone_telecom = fhir_patient.telecom.add()
        phone_telecom.system.value = codes_pb2.ContactPointSystemCode.PHONE
        phone_telecom.value.value = patient.user.phone_number
        phone_telecom.use.value = codes_pb2.ContactPointUseCode.MOBILE
    
    if patient.gender:
        gender_map = {
            'male': codes_pb2.AdministrativeGenderCode.MALE,
            'female': codes_pb2.AdministrativeGenderCode.FEMALE,
            'other': codes_pb2.AdministrativeGenderCode.OTHER,
            'unknown': codes_pb2.AdministrativeGenderCode.UNKNOWN
        }
        fhir_patient.gender.value = gender_map.get(patient.gender, codes_pb2.AdministrativeGenderCode.UNKNOWN)
    
    if patient.date_of_birth:
        import pytz
        utc = pytz.UTC
        birth_datetime = datetime.datetime.combine(patient.date_of_birth, datetime.time(0, 0))
        birth_datetime_utc = utc.localize(birth_datetime)
        fhir_patient.birth_date.value_us = int(birth_datetime_utc.timestamp() * 1000000)
        fhir_patient.birth_date.timezone = "UTC"
        fhir_patient.birth_date.precision = datatypes_pb2.Date.Precision.DAY
    
    if patient.user.address:
        address = fhir_patient.address.add()
        address.use.value = codes_pb2.AddressUseCode.HOME
        line = address.line.add()
        line.value = patient.user.address
        address.text.value = patient.user.address
    
    if patient.marital_status:
        marital_coding = fhir_patient.marital_status.coding.add()
        marital_coding.system.value = "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus"
        marital_coding.code.value = patient.marital_status
    
    if patient.language:
        communication = fhir_patient.communication.add()
        lang_coding = communication.language.coding.add()
        lang_coding.system.value = "urn:ietf:bcp:47"
        lang_coding.code.value = patient.language
        communication.preferred.value = True
    
    fhir_json = json_format.print_fhir_to_json_string(fhir_patient)
    
    return fhir_patient, fhir_json

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
        
class IsAdminOrDoctor(permissions.BasePermission):
    """
    Permission class to check if the user has admin or doctor role
    """
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False
        
        # Check if user has admin or doctor role
        return request.user.roles.filter(name__in=['admin', 'doctor']).exists()

class IsAdminOrAuthenticated(permissions.BasePermission):
    """
    Permission class that allows access to admin users or restricts to authenticated users
    based on the request method
    """
    def has_permission(self, request, view):
        # All users must be authenticated
        if not request.user.is_authenticated:
            return False
        
        # Admin users can do anything
        if request.user.roles.filter(name='admin').exists():
            return True
            
        # For safe methods (GET, HEAD, OPTIONS), any authenticated user can access
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # For unsafe methods (POST, PUT, DELETE), only allow if it's the user's own data
        # This check is done in has_object_permission for object-level views
        return False
        
    def has_object_permission(self, request, view, obj):
        # Admin users can do anything
        if request.user.roles.filter(name='admin').exists():
            return True
            
        # Allow users to manage their own data
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
            
        if obj == request.user:
            return True
            
        return False

class RoleListAPIView(APIView):
    # Allow unauthenticated users to list roles for registration forms
    # Use custom permission for POST operations - only admin can create roles
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        # Ensure only admin users can create roles
        if not request.user.is_authenticated or not request.user.roles.filter(name='admin').exists():
            return Response({"error": "Only administrators can create roles"}, status=status.HTTP_403_FORBIDDEN)
    
    def get(self, request):
        roles = Role.objects.all()
        serializer = RoleSerializer(roles, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = RoleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RoleDetailAPIView(APIView):
    permission_classes = [IsAdminUser]
    
    def get_object(self, pk):
        return get_object_or_404(Role, pk=pk)
    
    def get(self, request, pk):
        role = self.get_object(pk)
        serializer = RoleSerializer(role)
        return Response(serializer.data)
    
    def put(self, request, pk):
        role = self.get_object(pk)
        serializer = RoleSerializer(role, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        role = self.get_object(pk)
        role.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class UserListAPIView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        users = User.objects.all()
        
        # Filter by role if provided
        role = request.query_params.get('role')
        if role:
            users = users.filter(roles__name=role)
        
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDetailAPIView(APIView):
    permission_classes = [IsAdminOrAuthenticated]
    
    def get_object(self, pk):
        return get_object_or_404(User, pk=pk)
    
    def get(self, request, pk):
        user = self.get_object(pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
    def put(self, request, pk):
        user = self.get_object(pk)
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        user = self.get_object(pk)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class UserRegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    
    def get(self, request, format=None):
        """Provide available roles for the registration form (excluding admin)"""
        roles = Role.objects.exclude(name='admin')
        role_serializer = RoleSerializer(roles, many=True)
        
        # Also provide an empty serializer to expose form fields
        user_serializer = UserSerializer(context={'request': request})
        
        # Generate HTML for the role selection fields that will be shown in the browsable API
        role_options_html = ""
        for role in roles:
            role_options_html += f"""
            <div class="form-check">
                <input class="form-check-input" type="checkbox" name="role_names" value="{role.name}" id="role_{role.id}">
                <label class="form-check-label" for="role_{role.id}">
                    {role.name} - {role.description}
                </label>
            </div>
            """
        
        # Add HTML form guidance for the browsable API
        if request.accepted_renderer.format == 'api':
            return Response({
                'roles': role_serializer.data,
                'html_help': f"""
                <div class="card">
                    <div class="card-header">Registration Form Help</div>
                    <div class="card-body">
                        <h5 class="card-title">Available Roles</h5>
                        <p class="card-text">You can select one of the following roles:</p>
                        {role_options_html}
                        <hr>
                        <p>Admin role is not available for regular registration.</p>
                    </div>
                </div>
                """,
                'form_fields': {
                    'email': 'Your email address',
                    'password': 'Your password',
                    'first_name': 'Your first name',
                    'last_name': 'Your last name',
                    'phone_number': 'Your phone number',
                    'address': 'Your address',
                    'role_names': 'Select multiple roles from options above',
                    'role': 'Or specify a single role (doctor or patient)'
                }
            })
        
        # Regular JSON response for API clients
        return Response({
            'roles': role_serializer.data,
            'form_fields': {
                'email': 'Your email address',
                'password': 'Your password',
                'first_name': 'Your first name',
                'last_name': 'Your last name',
                'phone_number': 'Your phone number',
                'address': 'Your address',
                'role_names': 'List of role names (doctor, patient) [optional]',
                'role': 'Single role name (doctor or patient) [optional]'
            }
        })
    
    def post(self, request, format=None):
        serializer = UserSerializer(data=request.data, context={'request': request})
    
        
        if serializer.is_valid():
            user = serializer.save()
            
            if user.roles.filter(name='patient').exists():
                try:
                    patient = Patient.objects.get(user=user)
                    fhir_patient, fhir_json = create_fhir_patient(patient)
                    
                    fhir_json_pretty = json.dumps(json.loads(fhir_json), indent=2)
                    # Submit to Hapi Fhir server
                    
                    logger.info("=" * 80)
                    logger.info("FHIR PATIENT OBJECT CREATED FOR NEW REGISTRATION")
                    logger.info("=" * 80)
                    logger.info(f"Patient ID: {patient.id}")
                    logger.info(f"User Email: {user.email}")
                    logger.info(f"User Name: {user.get_full_name()}")
                    logger.info("-" * 80)
                    logger.info("FHIR JSON Representation:")
                    logger.info(fhir_json_pretty)
                    logger.info("=" * 80)
                    
                    print("\n" + "=" * 80)
                    print("FHIR PATIENT OBJECT CREATED FOR NEW REGISTRATION")
                    print("=" * 80)
                    print(f"Patient ID: {patient.id}")
                    print(f"User Email: {user.email}")
                    print(f"User Name: {user.get_full_name()}")
                    print("-" * 80)
                    print("FHIR JSON Representation:")
                    print(fhir_json_pretty)
                    print("=" * 80 + "\n")
                    
                except Patient.DoesNotExist:
                    logger.warning(f"Patient profile not found for user {user.email}")
                except Exception as e:
                    logger.error(f"Error creating FHIR patient object: {str(e)}")
            
            domain = os.environ.get('FRONTEND_DOMAIN', request.get_host())
            email_result = user.send_activation_email(domain)
            
            if email_result:
                message = 'Registration successful. Please check your email to activate your account.'
                logger.info(f"Activation email sent successfully to {user.email}")
            else:
                message = 'Registration successful. However, we encountered an issue sending the activation email. Please contact support.'
                logger.warning(f"Email sending failed for {user.email}, but user registration completed successfully")
            
            return Response({
                'detail': message,
                'user': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserActivateAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, uidb64, token):
        try:
            # Decode the user id
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            
            # Check the token is valid
            if default_token_generator.check_token(user, token):
                user.is_verified = True
                user.save()
                
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'detail': 'Account activated successfully!',
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Activation link is invalid or has expired!'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({
                'error': 'Activation link is invalid!'
            }, status=status.HTTP_400_BAD_REQUEST)

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class UserLoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Log in a user and obtain access token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description="Username or email"),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format="password", description="Password")
            }
        ),
        responses={
            200: openapi.Response("Success", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'refresh': openapi.Schema(type=openapi.TYPE_STRING, description="JWT refresh token"),
                    'access': openapi.Schema(type=openapi.TYPE_STRING, description="JWT access token"),
                    'user': openapi.Schema(type=openapi.TYPE_OBJECT, description="User details")
                }
            )),
            401: openapi.Response("Unauthorized", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'detail': openapi.Schema(type=openapi.TYPE_STRING, description="Error message")
                }
            ))
        }
    )
    def post(self, request):
        email = request.data.get('email') or request.data.get('username')
        password = request.data.get('password')

        print("Request data:", request.data)

        print(email)
        print(password)
        if not email or not password:
            return Response({
                'error': 'Please provide both email and password'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=email, password=password)
        
        if not user:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_verified:
            return Response({
                'error': 'Account not verified. Please check your email for the verification link.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        refresh = RefreshToken.for_user(user)
        
        # Add user roles to the token claims
        refresh['roles'] = [role.name for role in user.roles.all()]
        
        # Set token expiration time
        access_token = refresh.access_token
        refresh_token_lifetime = SIMPLE_JWT.get('REFRESH_TOKEN_LIFETIME', datetime.timedelta(days=14))
        access_token_lifetime = SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME', datetime.timedelta(minutes=60))
        
        expires_at = datetime.datetime.now() + access_token_lifetime
        refresh_expires_at = datetime.datetime.now() + refresh_token_lifetime
        
        # Serialize user with basic details
        user_serializer = UserSerializer(user)
        
        # Get role-specific data
        role_specific_data = {}
        
        # If user is a patient, include patient profile data
        if user.roles.filter(name='patient').exists():
            try:
                # Get or create patient profile
                patient, created = Patient.objects.get_or_create(user=user)
                
                # Log if a new profile was created
                if created:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"Created new patient profile for user {user.email} during login")
                
                patient_serializer = PatientSerializer(patient)
                role_specific_data['patient'] = patient_serializer.data
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error accessing patient profile during login: {str(e)}")
                role_specific_data['patient'] = None
        
        # If user is a doctor, include doctor profile data
        if user.roles.filter(name='doctor').exists():
            try:
                doctor = Doctor.objects.get(user=user)
                doctor_serializer = DoctorSerializer(doctor)
                role_specific_data['doctor'] = doctor_serializer.data
            except Doctor.DoesNotExist:
                role_specific_data['doctor'] = None
        
        # If user is a community health provider, include CHP profile data
        if user.roles.filter(name='community_health_provider').exists():
            try:
                # Get or create CHP profile
                chp, created = CommunityHealthProvider.objects.get_or_create(user=user)
                
                # Log if a new profile was created
                if created:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"Created new CHP profile for user {user.email} during login")
                
                chp_serializer = CommunityHealthProviderSerializer(chp)
                role_specific_data['community_health_provider'] = chp_serializer.data
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error accessing CHP profile during login: {str(e)}")
                role_specific_data['community_health_provider'] = None
        
        return Response({
            'access': str(access_token),
            'refresh': str(refresh),
            'user': user_serializer.data,
            'roles': [role.name for role in user.roles.all()],
            'role_data': role_specific_data,
            'expires_at': expires_at.isoformat(),
            'refresh_expires_at': refresh_expires_at.isoformat()
        }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_admin_user(request):
    """
    Special endpoint for registering the first admin user.
    This endpoint requires a secure token and can only be used once.
    """
    # Check if admin token is provided
    token = request.data.get('admin_token')
    if not token:
        return Response({
            'error': 'Admin registration token is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verify the token
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    if token_hash != ADMIN_TOKEN_HASH:
        return Response({
            'error': 'Invalid admin registration token'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Check if admin role exists, if not create it
    admin_role, created = Role.objects.get_or_create(
        name='admin',
        defaults={
            'description': 'Administrator with full system access',
            'is_system_role': True
        }
    )
    
    # Prepare user data
    user_data = request.data.copy()
    user_data['role_names'] = ['admin']  # Assign admin role
    user_data['role'] = 'admin'  # Satisfy the required field
    
    # If username is not provided, generate one from email
    if 'username' not in user_data:
        email = user_data.get('email', '')
        username = email.split('@')[0] if '@' in email else 'admin_user'
        user_data['username'] = username
    
    # Create admin user
    serializer = UserSerializer(data=user_data, context={'admin_registration': True})
    if serializer.is_valid():
        user = serializer.save()
        
        # Auto-verify admin user
        user.is_verified = True
        user.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'detail': 'Admin user registered successfully',
            'user': serializer.data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PatientListAPIView(APIView):
    """
    API endpoint to list all patients.
    Only accessible by admin and doctor users.
    """
    permission_classes = [IsAdminOrDoctor]
    
    def get(self, request):
        # Get patient role
        patient_role = get_object_or_404(Role, name='patient')
        
        # Get all users with patient role
        patients = Patient.objects.filter(user__roles=patient_role)
        
        # Apply filtering
        name = request.query_params.get('name')
        if name:
            patients = patients.filter(
                models.Q(user__first_name__icontains=name) | 
                models.Q(user__last_name__icontains=name)
            )
        
        # Serialize the data
        serializer = PatientSerializer(patients, many=True, context={'request': request})
        
        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        if request.query_params.get('format') == 'fhir':
            response["Content-Type"] = "application/fhir+json"
        
        return response

class PatientDetailAPIView(APIView):
    """
    API endpoint to get details of a specific patient.
    Only accessible by admin and doctor users.
    """
    permission_classes = [IsAdminOrDoctor]
    
    def get_object(self, pk):
        return get_object_or_404(Patient, pk=pk)
    
    def get(self, request, pk):
        patient = self.get_object(pk)
        serializer = PatientSerializer(patient, context={'request': request})
        
        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        if request.query_params.get('format') == 'fhir':
            response["Content-Type"] = "application/fhir+json"
        
        return response

class PatientProfileAPIView(APIView):
    """
    Endpoint for patients to view and update their own profile.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Check if user has patient role
        if not request.user.roles.filter(name='patient').exists():
            return Response({
                'error': 'Only patients can access this endpoint'
            }, status=status.HTTP_403_FORBIDDEN)
            
        try:
            # Get or create patient profile
            patient, created = Patient.objects.get_or_create(user=request.user)
            
            # Log if a new profile was created
            if created:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Created new patient profile for user {request.user.email}")
            
            serializer = PatientSerializer(patient, context={'request': request})
            
            # Set appropriate content type for FHIR responses
            response = Response(serializer.data)
            if request.query_params.get('format') == 'fhir':
                response["Content-Type"] = "application/fhir+json"
            
            return response
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error accessing patient profile: {str(e)}")
            return Response({
                'error': 'Error accessing patient profile'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request):
        # Check if user has patient role
        if not request.user.roles.filter(name='patient').exists():
            return Response({
                'error': 'Only patients can access this endpoint'
            }, status=status.HTTP_403_FORBIDDEN)
            
        try:
            # Get or create patient profile
            patient, created = Patient.objects.get_or_create(user=request.user)
            
            # Log if a new profile was created
            if created:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Created new patient profile for user {request.user.email} during PUT")
            
            serializer = PatientSerializer(patient, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating patient profile: {str(e)}")
            return Response({
                'error': 'Error updating patient profile'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def patch(self, request):
        # Check if user has patient role
        if not request.user.roles.filter(name='patient').exists():
            return Response({
                'error': 'Only patients can access this endpoint'
            }, status=status.HTTP_403_FORBIDDEN)
            
        try:
            # Get or create patient profile
            patient, created = Patient.objects.get_or_create(user=request.user)
            
            # Log if a new profile was created
            if created:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Created new patient profile for user {request.user.email} during PATCH")
            
            serializer = PatientSerializer(patient, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating patient profile: {str(e)}")
            return Response({
                'error': 'Error updating patient profile'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserProfileAPIView(APIView):
    """
    Unified endpoint for users to view their profile information.
    Returns both user details and role-specific profile information (patient or doctor).
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Get the base user data
        user = request.user
        user_serializer = UserSerializer(user)
        
        response_data = {
            'user': user_serializer.data,
            'roles': [role.name for role in user.roles.all()],
        }
        
        # Add role-specific profile data if available
        if user.roles.filter(name='patient').exists():
            try:
                # Get or create patient profile
                patient, created = Patient.objects.get_or_create(user=user)
                
                # Log if a new profile was created
                if created:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"Created new patient profile for user {user.email} during profile view")
                
                patient_serializer = PatientSerializer(patient, context={'request': request})
                response_data['patient_profile'] = patient_serializer.data
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error accessing patient profile: {str(e)}")
                response_data['patient_profile'] = None
        
        if user.roles.filter(name='doctor').exists():
            try:
                doctor = Doctor.objects.get(user=user)
                doctor_serializer = DoctorSerializer(doctor, context={'request': request})
                response_data['doctor_profile'] = doctor_serializer.data
            except Doctor.DoesNotExist:
                response_data['doctor_profile'] = None
        
        # Set appropriate content type for FHIR responses
        response = Response(response_data)
        if request.query_params.get('format') == 'fhir':
            response["Content-Type"] = "application/fhir+json"
        
        return response

class ResendVerificationAPIView(APIView):
    """
    Endpoint to resend verification email.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({
                'error': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            
            # Check if already verified
            if user.is_verified:
                return Response({
                    'message': 'Account is already verified'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Resend activation email
            domain = os.environ.get('FRONTEND_DOMAIN', request.get_host())
            user.send_activation_email(domain)
            
            return Response({
                'message': 'Verification email has been resent'
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            # Don't reveal if user exists
            return Response({
                'message': 'If an account with this email exists, a verification email has been sent'
            }, status=status.HTTP_200_OK)

class PasswordChangeAPIView(APIView):
    """
    Endpoint for users to change their password.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Get the validated data
            current_password = serializer.validated_data.get('current_password')
            new_password = serializer.validated_data.get('new_password')
            
            # Check if current password is correct
            if not request.user.check_password(current_password):
                return Response({
                    'error': 'Current password is incorrect'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Set the new password
            request.user.set_password(new_password)
            request.user.save()
            
            # Update session auth hash to prevent logout
            update_session_auth_hash(request, request.user)
            
            return Response({
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EmailChangeAPIView(APIView):
    """
    Endpoint for users to change their email.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = EmailChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Get the validated data
            password = serializer.validated_data.get('password')
            new_email = serializer.validated_data.get('new_email')
            
            # Check if password is correct
            if not request.user.check_password(password):
                return Response({
                    'error': 'Password is incorrect'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if email is already in use
            if User.objects.filter(email=new_email).exclude(id=request.user.id).exists():
                return Response({
                    'error': 'Email is already in use'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update email
            request.user.email = new_email
            request.user.save()
            
            return Response({
                'message': 'Email changed successfully',
                'new_email': new_email
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PhoneChangeAPIView(APIView):
    """
    Endpoint for users to change their phone number.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PhoneChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Get the validated data
            password = serializer.validated_data.get('password')
            new_phone_number = serializer.validated_data.get('new_phone_number')
            
            # Check if password is correct
            if not request.user.check_password(password):
                return Response({
                    'error': 'Password is incorrect'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update phone number
            request.user.phone_number = new_phone_number
            request.user.save()
            
            return Response({
                'message': 'Phone number changed successfully',
                'new_phone_number': new_phone_number
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ContactUsAPIView(APIView):
    """
    Endpoint for users to submit contact form.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = ContactUsSerializer(data=request.data)
        if serializer.is_valid():
            # In a real implementation, you would save the message or send an email
            name = serializer.validated_data.get('name')
            email = serializer.validated_data.get('email')
            message = serializer.validated_data.get('message')
            
            logger = logging.getLogger(__name__)
            logger.info(f"Contact form submission from {name} ({email}): {message}")
            
            return Response({
                'message': 'Your message has been sent. We will get back to you soon!'
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SupportRequestAPIView(APIView):
    """
    Endpoint for authenticated users to submit support requests.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = SupportRequestSerializer(data=request.data)
        if serializer.is_valid():
            # In a real implementation, you would save the request or create a ticket
            issue_type = serializer.validated_data.get('issue_type')
            subject = serializer.validated_data.get('subject')
            description = serializer.validated_data.get('description')
            
            # Create a unique support ticket ID
            ticket_id = f"SUP-{secrets.token_hex(4).upper()}"
            
            logger = logging.getLogger(__name__)
            logger.info(f"Support request from {request.user.email}, Ticket: {ticket_id}, Type: {issue_type}, Subject: {subject}")
            
            return Response({
                'message': 'Your support request has been submitted',
                'ticket_id': ticket_id
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordAPIView(APIView):
    """
    Endpoint to initiate password reset process.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            
            try:
                user = User.objects.get(email=email)
                
                # Generate password reset token
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                
                # Get domain for reset link
                domain = os.environ.get('FRONTEND_DOMAIN', request.get_host())
                
                # Use HTTPS if available
                protocol = 'https' if request.is_secure() else 'http'
                if domain != request.get_host():
                    protocol = 'https'
                    
                # Create password reset URL
                reset_url = f"{protocol}://{domain}/reset-password/{uid}/{token}/"
                
                # Send password reset email - would integrate with your email system
                # For now, we'll just log it
                logger = logging.getLogger(__name__)
                logger.info(f"Password reset requested for {email}. Reset URL: {reset_url}")
                
                # In a real implementation, you would send an email like:
                # send_mail(
                #     'Reset Your Password',
                #     f'Click the link to reset your password: {reset_url}',
                #     settings.DEFAULT_FROM_EMAIL,
                #     [email],
                #     fail_silently=False,
                # )
                
            except User.DoesNotExist:
                # Don't reveal if user exists
                pass
                
            # Always return success to prevent email enumeration
            return Response({
                'message': 'If an account with this email exists, a password reset link has been sent.'
            }, status=status.HTTP_200_OK)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordAPIView(APIView):
    """
    Endpoint to reset password using the token sent via email.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, uidb64, token):
        try:
            # Decode the user id
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            
            # Check the token is valid
            if default_token_generator.check_token(user, token):
                # Get the new password
                new_password = request.data.get('new_password')
                if not new_password:
                    return Response({
                        'error': 'New password is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Validate the new password
                try:
                    validate_password(new_password)
                except ValidationError as e:
                    return Response({
                        'error': list(e.messages)
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Set the new password
                user.set_password(new_password)
                user.save()
                
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'message': 'Password has been reset successfully',
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Reset link is invalid or has expired'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({
                'error': 'Reset link is invalid'
            }, status=status.HTTP_400_BAD_REQUEST)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing audit logs. Admin users only.
    Provides list, retrieve, filtering, search, and export functionality.
    """
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email_address', 'activity', 'role']
    filterset_fields = ['activity', 'status', 'role']
    ordering_fields = ['created_at', 'last_active', 'username']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Apply custom filtering based on query parameters
        """
        queryset = super().get_queryset()
        
        # Apply date filtering
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            try:
                from datetime import datetime
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=date_from)
            except ValueError:
                pass
                
        if date_to:
            try:
                from datetime import datetime
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=date_to)
            except ValueError:
                pass
        
        return queryset
    
    @action(detail=False, methods=['get'], url_path='export-csv')
    def export_csv(self, request):
        """
        Export audit logs to CSV format
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="audit_logs_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'Username', 'Activity', 'Email Address', 'Role', 'Time Spent', 
            'Date Joined', 'Last Active', 'Status', 'IP Address', 'Created At'
        ])
        
        # Write data
        for log in queryset:
            writer.writerow([
                log.username,
                log.get_activity_display(),
                log.email_address,
                log.role,
                log.formatted_time_spent,
                log.date_joined.strftime('%Y-%m-%d %H:%M:%S') if log.date_joined else '',
                log.last_active.strftime('%Y-%m-%d %H:%M:%S') if log.last_active else '',
                log.get_status_display(),
                log.ip_address or '',
                log.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    
    @action(detail=False, methods=['get'], url_path='export-pdf')
    def export_pdf(self, request):
        """
        Export audit logs to PDF format (simplified implementation)
        For a full PDF implementation, consider using libraries like ReportLab
        """
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        
        queryset = self.filter_queryset(self.get_queryset())[:100]  # Limit for PDF
        
        # For now, return a simple HTML that can be printed as PDF
        # In production, you'd use a proper PDF library
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Audit Logs Export</title>
            <style>
                body {{ font-family: Arial, sans-serif; font-size: 12px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; font-weight: bold; }}
                .header {{ text-align: center; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Panacare - Audit Logs Report</h1>
                <p>Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Username</th>
                        <th>Activity</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Status</th>
                        <th>Created At</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for log in queryset:
            html_content += f"""
                    <tr>
                        <td>{log.username}</td>
                        <td>{log.get_activity_display()}</td>
                        <td>{log.email_address}</td>
                        <td>{log.role}</td>
                        <td>{log.get_status_display()}</td>
                        <td>{log.created_at.strftime('%Y-%m-%d %H:%M:%S')}</td>
                    </tr>
            """
        
        html_content += """
                </tbody>
            </table>
        </body>
        </html>
        """
        
        response = HttpResponse(html_content, content_type='text/html')
        response['Content-Disposition'] = f'attachment; filename="audit_logs_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.html"'
        
        return response
    
    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        """
        Get audit log statistics
        """
        queryset = self.get_queryset()
        
        # Calculate statistics
        from django.db.models import Count
        from datetime import datetime, timedelta
        
        total_logs = queryset.count()
        today_logs = queryset.filter(created_at__date=datetime.now().date()).count()
        week_logs = queryset.filter(created_at__gte=datetime.now() - timedelta(days=7)).count()
        
        # Activity breakdown
        activity_stats = queryset.values('activity').annotate(count=Count('activity')).order_by('-count')[:10]
        
        # Status breakdown
        status_stats = queryset.values('status').annotate(count=Count('status'))
        
        # Role breakdown
        role_stats = queryset.values('role').annotate(count=Count('role')).order_by('-count')[:10]
        
        return Response({
            'total_logs': total_logs,
            'today_logs': today_logs,
            'week_logs': week_logs,
            'activity_breakdown': list(activity_stats),
            'status_breakdown': list(status_stats),
            'role_breakdown': list(role_stats)
        })


class CountiesListAPIView(APIView):
    """
    API view to list all counties
    """
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get list of all counties for location hierarchy selection. This is the first level in the County → Sub-county → Ward → Village hierarchy.",
        responses={
            200: openapi.Response("Success", openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid", example="550e8400-e29b-41d4-a716-446655440000"),
                        'name': openapi.Schema(type=openapi.TYPE_STRING, example="Nairobi")
                    }
                )
            ))
        },
        tags=['Location Hierarchy']
    )
    def get(self, request):
        LocationService.ensure_locations_exist()
        counties = LocationService.get_counties()
        return Response(counties, status=status.HTTP_200_OK)


class SubCountiesListAPIView(APIView):
    """
    API view to list subcounties, optionally filtered by county
    """
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get list of subcounties, optionally filtered by county_id. This is the second level in the location hierarchy.",
        manual_parameters=[
            openapi.Parameter('county_id', openapi.IN_QUERY, description="Filter by county UUID", type=openapi.TYPE_STRING, format="uuid", example="550e8400-e29b-41d4-a716-446655440000")
        ],
        responses={
            200: openapi.Response("Success", openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid", example="550e8400-e29b-41d4-a716-446655440010"),
                        'name': openapi.Schema(type=openapi.TYPE_STRING, example="Westlands"),
                        'parent_id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid", example="550e8400-e29b-41d4-a716-446655440000")
                    }
                )
            ))
        },
        tags=['Location Hierarchy']
    )
    def get(self, request):
        county_id = request.query_params.get('county_id')
        LocationService.ensure_locations_exist()
        subcounties = LocationService.get_subcounties(county_id)
        return Response(subcounties, status=status.HTTP_200_OK)


class WardsListAPIView(APIView):
    """
    API view to list wards, optionally filtered by subcounty
    """
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get list of wards, optionally filtered by subcounty_id. This is the third level in the location hierarchy.",
        manual_parameters=[
            openapi.Parameter('subcounty_id', openapi.IN_QUERY, description="Filter by subcounty UUID", type=openapi.TYPE_STRING, format="uuid", example="550e8400-e29b-41d4-a716-446655440010")
        ],
        responses={
            200: openapi.Response("Success", openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid", example="550e8400-e29b-41d4-a716-446655440020"),
                        'name': openapi.Schema(type=openapi.TYPE_STRING, example="Parklands"),
                        'parent_id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid", example="550e8400-e29b-41d4-a716-446655440010")
                    }
                )
            ))
        },
        tags=['Location Hierarchy']
    )
    def get(self, request):
        subcounty_id = request.query_params.get('subcounty_id')
        LocationService.ensure_locations_exist()
        wards = LocationService.get_wards(subcounty_id)
        return Response(wards, status=status.HTTP_200_OK)


class VillagesListAPIView(APIView):
    """
    API view to list villages, optionally filtered by ward
    """
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get list of villages, optionally filtered by ward_id. This is the fourth and final level in the location hierarchy.",
        manual_parameters=[
            openapi.Parameter('ward_id', openapi.IN_QUERY, description="Filter by ward UUID", type=openapi.TYPE_STRING, format="uuid", example="550e8400-e29b-41d4-a716-446655440020")
        ],
        responses={
            200: openapi.Response("Success", openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid", example="550e8400-e29b-41d4-a716-446655440030"),
                        'name': openapi.Schema(type=openapi.TYPE_STRING, example="Highridge"),
                        'parent_id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid", example="550e8400-e29b-41d4-a716-446655440020")
                    }
                )
            ))
        },
        tags=['Location Hierarchy']
    )
    def get(self, request):
        ward_id = request.query_params.get('ward_id')
        LocationService.ensure_locations_exist()
        villages = LocationService.get_villages(ward_id)
        return Response(villages, status=status.HTTP_200_OK)


class LocationHierarchyAPIView(APIView):
    """
    API view to get full location hierarchy for a given location
    """
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get full location hierarchy for a location. Returns the complete path from county to village for a given location.",
        manual_parameters=[
            openapi.Parameter('location_id', openapi.IN_QUERY, description="Location UUID", type=openapi.TYPE_STRING, format="uuid", required=True, example="550e8400-e29b-41d4-a716-446655440030")
        ],
        responses={
            200: openapi.Response("Success", openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid", example="550e8400-e29b-41d4-a716-446655440030"),
                        'name': openapi.Schema(type=openapi.TYPE_STRING, example="Highridge"),
                        'level': openapi.Schema(type=openapi.TYPE_STRING, enum=['county', 'sub_county', 'ward', 'village'], example="village")
                    }
                )
            )),
            400: openapi.Response("Bad Request", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'error': openapi.Schema(type=openapi.TYPE_STRING, example="location_id is required")}
            ))
        },
        tags=['Location Hierarchy']
    )
    def get(self, request):
        location_id = request.query_params.get('location_id')
        if not location_id:
            return Response({'error': 'location_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        hierarchy = LocationService.get_location_hierarchy(location_id)
        return Response(hierarchy, status=status.HTTP_200_OK)


class SyncLocationsAPIView(APIView):
    """
    API view to sync locations from external API (admin only)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Sync location data from external Kenya Areas API (admin only). This populates the location hierarchy with current data.",
        responses={
            200: openapi.Response("Success", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'message': openapi.Schema(type=openapi.TYPE_STRING, example="Locations synced successfully")}
            )),
            403: openapi.Response("Forbidden", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'error': openapi.Schema(type=openapi.TYPE_STRING, example="Admin access required")}
            )),
            500: openapi.Response("Internal Server Error", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'error': openapi.Schema(type=openapi.TYPE_STRING, example="Failed to sync locations")}
            ))
        },
        tags=['Location Hierarchy']
    )
    def post(self, request):
        if not request.user.is_staff:
            return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            success = LocationService.sync_locations_from_api()
            if success:
                return Response({'message': 'Locations synced successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Failed to sync locations'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Error syncing locations: {e}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CHPPatientCreateAPIView(APIView):
    """
    API view for Community Health Provider to create patients
    Supports both authenticated and offline modes
    """
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Create a new patient as a Community Health Provider. Supports both authenticated and offline modes. In offline mode, provide 'chp_id' in the request body.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'chp_id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid", description="CHP ID for offline mode (optional if authenticated)", example="550e8400-e29b-41d4-a716-446655440400"),
                'patient_id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid", description="Pre-generated patient UUID for offline mode (optional)", example="550e8400-e29b-41d4-a716-446655440500"),
                'user_id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid", description="Pre-generated user UUID for offline mode (optional)", example="550e8400-e29b-41d4-a716-446655440501"),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, example="Mary"),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, example="Wanjiku"),
                'email': openapi.Schema(type=openapi.TYPE_STRING, example="mary.wanjiku@example.com"),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, example="+254722333444"),
                'location_id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid", example="550e8400-e29b-41d4-a716-446655440030"),
                'date_of_birth': openapi.Schema(type=openapi.TYPE_STRING, format="date", example="1985-03-15"),
                'gender': openapi.Schema(type=openapi.TYPE_STRING, enum=['male', 'female', 'other', 'unknown'], example="female"),
                'blood_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'], example="O+"),
                'allergies': openapi.Schema(type=openapi.TYPE_STRING, example="Penicillin"),
                'medical_conditions': openapi.Schema(type=openapi.TYPE_STRING, example="Diabetes Type 2"),
                'medications': openapi.Schema(type=openapi.TYPE_STRING, example="Metformin 500mg"),
                'height_cm': openapi.Schema(type=openapi.TYPE_INTEGER, example=165),
                'weight_kg': openapi.Schema(type=openapi.TYPE_NUMBER, example=65.5),
                'emergency_contact_name': openapi.Schema(type=openapi.TYPE_STRING, example="John Wanjiku"),
                'emergency_contact_phone': openapi.Schema(type=openapi.TYPE_STRING, example="+254722555666"),
                'emergency_contact_relationship': openapi.Schema(type=openapi.TYPE_STRING, example="Spouse")
            },
            required=['first_name', 'last_name', 'email', 'phone_number']
        ),
        responses={
            201: openapi.Response("Patient created successfully", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, example="Patient created successfully"),
                    'patient_id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid", example="550e8400-e29b-41d4-a716-446655440300"),
                    'user_id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid", example="550e8400-e29b-41d4-a716-446655440301"),
                    'temporary_password': openapi.Schema(type=openapi.TYPE_STRING, example="TempPass789"),
                    'note': openapi.Schema(type=openapi.TYPE_STRING, example="Please provide the temporary password to the patient for first login")
                }
            )),
            400: openapi.Response("Bad Request", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, example="User with this ID already exists")
                }
            )),
            404: openapi.Response("Not Found", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, example="Community Health Provider not found")
                }
            ))
        },
        tags=['Community Health Provider']
    )
    def post(self, request):
        # Determine if this is offline mode (CHP ID provided) or authenticated mode
        chp_id = request.data.get('chp_id')
        chp = None
        
        if chp_id:
            # Offline mode: Use provided CHP ID
            try:
                chp = CommunityHealthProvider.objects.get(id=chp_id)
            except CommunityHealthProvider.DoesNotExist:
                return Response({'error': 'Community Health Provider not found'}, 
                              status=status.HTTP_404_NOT_FOUND)
        elif request.user and request.user.is_authenticated:
            # Authenticated mode: Use authenticated user's CHP profile
            try:
                chp = CommunityHealthProvider.objects.get(user=request.user)
            except CommunityHealthProvider.DoesNotExist:
                return Response({'error': 'Only Community Health Providers can create patients'}, 
                              status=status.HTTP_403_FORBIDDEN)
        else:
            # Neither CHP ID provided nor authenticated
            return Response({'error': 'CHP ID is required for offline mode'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Create a copy of request data without chp_id for the serializer
        patient_data = request.data.copy()
        if 'chp_id' in patient_data:
            del patient_data['chp_id']
        
        serializer = CHPPatientCreateSerializer(data=patient_data, context={'chp': chp})
        if serializer.is_valid():
            result = serializer.save()
            
            return Response({
                'message': 'Patient created successfully',
                'patient_id': str(result['patient'].id),
                'user_id': str(result['user'].id),
                'temporary_password': result['temporary_password'],
                'note': 'Please provide the temporary password to the patient for first login',
                'chp_info': {
                    'id': str(chp.id),
                    'name': chp.user.get_full_name(),
                    'service_area': chp.service_area
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CHPClinicalDecisionSupportAPIView(APIView):
    """
    API view for Community Health Provider to perform CDSS on behalf of patients
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Perform Clinical Decision Support System analysis on behalf of a patient. Analyzes vital signs, symptoms, and medical history to provide risk assessment and recommendations.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['patient_id'],
            properties={
                'patient_id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid", description="UUID of the patient", example="550e8400-e29b-41d4-a716-446655440300"),
                'age': openapi.Schema(type=openapi.TYPE_INTEGER, minimum=1, maximum=120, example=35),
                'gender': openapi.Schema(type=openapi.TYPE_STRING, enum=['male', 'female', 'other'], example='female'),
                'weight': openapi.Schema(type=openapi.TYPE_NUMBER, description="Weight in kg", example=65.5),
                'height': openapi.Schema(type=openapi.TYPE_NUMBER, description="Height in cm", example=165),
                'high_blood_pressure': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                'diabetes': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                'on_medication': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                'headache': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                'dizziness': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                'blurred_vision': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                'chest_pain': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                'shortness_of_breath': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                'nausea': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                'fatigue': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                'systolic_bp': openapi.Schema(type=openapi.TYPE_INTEGER, description="Systolic blood pressure", example=125),
                'diastolic_bp': openapi.Schema(type=openapi.TYPE_INTEGER, description="Diastolic blood pressure", example=80),
                'blood_sugar': openapi.Schema(type=openapi.TYPE_NUMBER, description="Blood sugar level (mg/dL)", example=180),
                'heart_rate': openapi.Schema(type=openapi.TYPE_INTEGER, description="Heart rate (bpm)", example=72)
            }
        ),
        responses={
            200: openapi.Response("CDSS analysis completed", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid"),
                    'analysis': openapi.Schema(type=openapi.TYPE_STRING),
                    'risk_level': openapi.Schema(type=openapi.TYPE_STRING, enum=['low', 'medium', 'high', 'critical']),
                    'bmi': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'bmi_category': openapi.Schema(type=openapi.TYPE_STRING),
                    'blood_pressure_status': openapi.Schema(type=openapi.TYPE_STRING),
                    'blood_sugar_status': openapi.Schema(type=openapi.TYPE_STRING),
                    'heart_rate_status': openapi.Schema(type=openapi.TYPE_STRING),
                    'recommendations': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                    'chp_id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid"),
                    'chp_name': openapi.Schema(type=openapi.TYPE_STRING),
                    'patient_id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid"),
                    'patient_name': openapi.Schema(type=openapi.TYPE_STRING),
                    'created_at': openapi.Schema(type=openapi.TYPE_STRING, format="date-time")
                }
            )),
            400: openapi.Response("Bad Request", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'error': openapi.Schema(type=openapi.TYPE_STRING, example="patient_id is required")}
            )),
            403: openapi.Response("Permission Denied", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'error': openapi.Schema(type=openapi.TYPE_STRING, example="Only Community Health Providers can perform CDSS")}
            )),
            404: openapi.Response("Patient not found", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'error': openapi.Schema(type=openapi.TYPE_STRING, example="Patient not found")}
            ))
        },
        tags=['Community Health Provider']
    )
    def post(self, request):
        # Check if user is a Community Health Provider
        try:
            chp = CommunityHealthProvider.objects.get(user=request.user)
        except CommunityHealthProvider.DoesNotExist:
            return Response({'error': 'Only Community Health Providers can perform CDSS'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        patient_id = request.data.get('patient_id')
        if not patient_id:
            return Response({'error': 'patient_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Import and use existing CDSS functionality
        from clinical_support.models import ClinicalDecisionRecord
        from clinical_support.views import ClinicalDecisionSupportAPIView as BaseCDSS
        
        # Create CDSS record with CHP context
        cdss_data = request.data.copy()
        cdss_data.pop('patient_id', None)  # Remove patient_id as it's not part of CDSS model
        
        # Create the CDSS record
        try:
            # Use the existing CDSS logic
            base_cdss = BaseCDSS()
            
            # Temporarily modify request to include patient info
            original_user = request.user
            request.user = patient.user  # Set to patient for CDSS processing
            
            response = base_cdss.post(request)
            
            # Restore original user
            request.user = original_user
            
            if response.status_code == 201:
                response_data = response.data
                response_data['chp_id'] = str(chp.id)
                response_data['chp_name'] = chp.user.get_full_name()
                response_data['patient_id'] = str(patient.id)
                response_data['patient_name'] = patient.user.get_full_name()
                
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return response
                
        except Exception as e:
            logger.error(f"Error in CHP CDSS: {e}")
            return Response({'error': 'Failed to perform CDSS analysis'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CHPDoctorAvailabilityAPIView(APIView):
    """
    API view for Community Health Provider to view available doctors with filtering
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Search for available doctors with comprehensive filtering options. Returns doctors with their availability schedules, contact information, and location details.",
        manual_parameters=[
            openapi.Parameter('name', openapi.IN_QUERY, description="Search by doctor's name (partial matches supported)", type=openapi.TYPE_STRING, example="smith"),
            openapi.Parameter('specialty', openapi.IN_QUERY, description="Filter by medical specialty", type=openapi.TYPE_STRING, example="cardiology"),
            openapi.Parameter('location_id', openapi.IN_QUERY, description="Filter by location UUID", type=openapi.TYPE_STRING, format="uuid", example="550e8400-e29b-41d4-a716-446655440030"),
            openapi.Parameter('weekday', openapi.IN_QUERY, description="Filter by weekday (0=Monday, 6=Sunday)", type=openapi.TYPE_INTEGER, enum=[0,1,2,3,4,5,6], example=1),
            openapi.Parameter('time_slot', openapi.IN_QUERY, description="Filter by specific time slot (HH:MM format)", type=openapi.TYPE_STRING, example="14:00"),
            openapi.Parameter('date', openapi.IN_QUERY, description="Filter by specific date (YYYY-MM-DD format)", type=openapi.TYPE_STRING, format="date", example="2025-12-20")
        ],
        responses={
            200: openapi.Response("Available doctors list", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER, example=2),
                    'doctors': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid"),
                                'name': openapi.Schema(type=openapi.TYPE_STRING, example="Dr. John Smith"),
                                'specialty': openapi.Schema(type=openapi.TYPE_STRING, example="Cardiology"),
                                'experience_years': openapi.Schema(type=openapi.TYPE_INTEGER, example=12),
                                'license_number': openapi.Schema(type=openapi.TYPE_STRING, example="MD001234"),
                                'consultation_fee': openapi.Schema(type=openapi.TYPE_STRING, example="8000.00"),
                                'contact': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'email': openapi.Schema(type=openapi.TYPE_STRING, example="dr.smith@hospital.co.ke"),
                                        'phone': openapi.Schema(type=openapi.TYPE_STRING, example="+254722111333")
                                    }
                                ),
                                'location': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid"),
                                        'name': openapi.Schema(type=openapi.TYPE_STRING, example="Parklands"),
                                        'level': openapi.Schema(type=openapi.TYPE_STRING, example="ward")
                                    }
                                ),
                                'availability': openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'weekday': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                            'weekday_name': openapi.Schema(type=openapi.TYPE_STRING, example="Tuesday"),
                                            'start_time': openapi.Schema(type=openapi.TYPE_STRING, example="09:00"),
                                            'end_time': openapi.Schema(type=openapi.TYPE_STRING, example="17:00")
                                        }
                                    )
                                )
                            }
                        )
                    )
                }
            )),
            400: openapi.Response("Bad Request", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'error': openapi.Schema(type=openapi.TYPE_STRING, example="Invalid date format. Use YYYY-MM-DD")}
            )),
            403: openapi.Response("Permission Denied", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'error': openapi.Schema(type=openapi.TYPE_STRING, example="Only Community Health Providers can view doctor availability")}
            ))
        },
        tags=['Community Health Provider']
    )
    def get(self, request):
        # Check if user is a Community Health Provider
        try:
            chp = CommunityHealthProvider.objects.get(user=request.user)
        except CommunityHealthProvider.DoesNotExist:
            return Response({'error': 'Only Community Health Providers can view doctor availability'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        from doctors.models import Doctor
        from healthcare.models import DoctorAvailability
        from django.db.models import Q
        from datetime import datetime
        
        # Base query for active and verified doctors
        doctors_query = Doctor.objects.filter(is_available=True, is_verified=True)
        
        # Apply filters
        name = request.query_params.get('name')
        if name:
            doctors_query = doctors_query.filter(
                Q(user__first_name__icontains=name) | 
                Q(user__last_name__icontains=name) |
                Q(user__username__icontains=name)
            )
        
        specialty = request.query_params.get('specialty')
        if specialty:
            doctors_query = doctors_query.filter(specialty__icontains=specialty)
        
        location_id = request.query_params.get('location_id')
        if location_id:
            doctors_query = doctors_query.filter(user__location_id=location_id)
        
        # Get availability filters
        weekday = request.query_params.get('weekday')
        time_slot = request.query_params.get('time_slot')
        date_filter = request.query_params.get('date')
        
        # If date is provided, calculate weekday
        if date_filter:
            try:
                date_obj = datetime.strptime(date_filter, '%Y-%m-%d')
                weekday = str(date_obj.weekday())  # Monday is 0
            except ValueError:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        
        doctors = doctors_query.distinct()
        
        # Prepare response data
        doctors_data = []
        for doctor in doctors:
            doctor_data = {
                'id': str(doctor.id),
                'name': doctor.user.get_full_name(),
                'specialty': doctor.specialty,
                'experience_years': doctor.experience_years,
                'license_number': doctor.license_number,
                'bio': doctor.bio,
                'contact': {
                    'email': doctor.user.email,
                    'phone': doctor.user.phone_number
                },
                'location': None,
                'availability': []
            }
            
            # Add location info if available
            if doctor.user.location:
                doctor_data['location'] = {
                    'id': str(doctor.user.location.id),
                    'name': doctor.user.location.name,
                    'level': doctor.user.location.level
                }
            
            # Get availability
            availability_query = DoctorAvailability.objects.filter(
                doctor=doctor, is_available=True
            )
            
            if weekday is not None:
                availability_query = availability_query.filter(weekday=int(weekday))
            
            if time_slot:
                try:
                    time_obj = datetime.strptime(time_slot, '%H:%M').time()
                    availability_query = availability_query.filter(
                        start_time__lte=time_obj,
                        end_time__gte=time_obj
                    )
                except ValueError:
                    return Response({'error': 'Invalid time format. Use HH:MM'}, 
                                  status=status.HTTP_400_BAD_REQUEST)
            
            for availability in availability_query:
                doctor_data['availability'].append({
                    'weekday': availability.weekday,
                    'weekday_name': availability.get_weekday_display(),
                    'start_time': availability.start_time.strftime('%H:%M'),
                    'end_time': availability.end_time.strftime('%H:%M')
                })
            
            # Only include doctors with availability if time filters are applied
            if weekday is not None or time_slot:
                if doctor_data['availability']:
                    doctors_data.append(doctor_data)
            else:
                doctors_data.append(doctor_data)
        
        return Response({
            'count': len(doctors_data),
            'doctors': doctors_data
        }, status=status.HTTP_200_OK)


class CHPAppointmentBookingAPIView(APIView):
    """
    API view for Community Health Provider to book appointments on behalf of patients
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Book an appointment on behalf of a patient. Validates doctor availability, checks for conflicts, and creates a 30-minute appointment slot.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['patient_id', 'doctor_id', 'appointment_date', 'appointment_time'],
            properties={
                'patient_id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid", description="UUID of the patient", example="550e8400-e29b-41d4-a716-446655440300"),
                'doctor_id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid", description="UUID of the doctor", example="550e8400-e29b-41d4-a716-446655440600"),
                'appointment_date': openapi.Schema(type=openapi.TYPE_STRING, format="date", description="Date in YYYY-MM-DD format", example="2025-12-20"),
                'appointment_time': openapi.Schema(type=openapi.TYPE_STRING, description="Time in HH:MM format (24-hour)", example="14:30"),
                'appointment_type': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    enum=['routine', 'follow-up', 'emergency', 'consultation', 'procedure', 'checkup', 'other'],
                    default='consultation',
                    description="Type of appointment",
                    example='consultation'
                ),
                'notes': openapi.Schema(type=openapi.TYPE_STRING, description="Additional notes for the appointment", example="Follow-up for diabetes management"),
                'symptoms': openapi.Schema(type=openapi.TYPE_STRING, description="Patient's symptoms or reason for visit", example="Dizziness and fatigue after meals"),
                'urgency_level': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['low', 'medium', 'high', 'critical'],
                    default='medium',
                    description="Priority level of the appointment",
                    example='medium'
                )
            }
        ),
        responses={
            201: openapi.Response("Appointment booked successfully", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, example="Appointment booked successfully"),
                    'appointment_id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid", example="550e8400-e29b-41d4-a716-446655440700"),
                    'appointment_details': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'patient_name': openapi.Schema(type=openapi.TYPE_STRING, example="Mary Wanjiku"),
                            'doctor_name': openapi.Schema(type=openapi.TYPE_STRING, example="Dr. John Smith"),
                            'date': openapi.Schema(type=openapi.TYPE_STRING, example="2025-12-20"),
                            'time': openapi.Schema(type=openapi.TYPE_STRING, example="14:30"),
                            'type': openapi.Schema(type=openapi.TYPE_STRING, example="consultation"),
                            'status': openapi.Schema(type=openapi.TYPE_STRING, example="BOOKED"),
                            'chp_name': openapi.Schema(type=openapi.TYPE_STRING, example="Nurse Jane Doe")
                        }
                    )
                }
            )),
            400: openapi.Response("Bad Request", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'error': openapi.Schema(type=openapi.TYPE_STRING, example="Doctor is not available at the requested time")}
            )),
            403: openapi.Response("Permission Denied", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'error': openapi.Schema(type=openapi.TYPE_STRING, example="Only Community Health Providers can book appointments")}
            )),
            404: openapi.Response("Patient or Doctor not found", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'error': openapi.Schema(type=openapi.TYPE_STRING, example="Patient not found")}
            ))
        },
        tags=['Community Health Provider']
    )
    def post(self, request):
        # Check if user is a Community Health Provider
        try:
            chp = CommunityHealthProvider.objects.get(user=request.user)
        except CommunityHealthProvider.DoesNotExist:
            return Response({'error': 'Only Community Health Providers can book appointments'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        from healthcare.models import Appointment, HealthCare
        from doctors.models import Doctor
        from datetime import datetime, time
        
        # Extract data
        patient_id = request.data.get('patient_id')
        doctor_id = request.data.get('doctor_id')
        appointment_date = request.data.get('appointment_date')
        appointment_time = request.data.get('appointment_time')
        appointment_type = request.data.get('appointment_type', 'routine')
        notes = request.data.get('notes', '')
        symptoms = request.data.get('symptoms', '')
        urgency_level = request.data.get('urgency_level', 'medium')
        
        # Validation
        if not all([patient_id, doctor_id, appointment_date, appointment_time]):
            return Response({'error': 'patient_id, doctor_id, appointment_date, and appointment_time are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            return Response({'error': 'Doctor not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Parse date and time
        try:
            date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            time_obj = datetime.strptime(appointment_time, '%H:%M').time()
            appointment_datetime = datetime.combine(date_obj, time_obj)
        except ValueError:
            return Response({'error': 'Invalid date or time format. Use YYYY-MM-DD for date and HH:MM for time'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Check doctor availability for the requested time
        from healthcare.models import DoctorAvailability
        weekday = date_obj.weekday()
        
        availability = DoctorAvailability.objects.filter(
            doctor=doctor,
            weekday=weekday,
            start_time__lte=time_obj,
            end_time__gte=time_obj,
            is_available=True
        ).first()
        
        if not availability:
            return Response({'error': 'Doctor is not available at the requested time'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Check for existing appointments at the same time
        # Assume 30-minute appointment slots
        from datetime import timedelta
        end_time_obj = (datetime.combine(date_obj, time_obj) + timedelta(minutes=30)).time()
        
        existing_appointment = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=date_obj,
            start_time=time_obj,
            status__in=['BOOKED', 'SCHEDULED', 'ARRIVED']
        ).exists()
        
        if existing_appointment:
            return Response({'error': 'Doctor already has an appointment at this time'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create default healthcare facility
        healthcare_facility = HealthCare.objects.first()  # You might want to improve this logic
        
        try:
            # Create appointment
            appointment = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                healthcare_facility=healthcare_facility,
                appointment_date=date_obj,
                start_time=time_obj,
                end_time=end_time_obj,
                appointment_type=appointment_type,
                status='BOOKED',
                notes=notes,
                reason=symptoms,  # Use reason field for symptoms
                risk_level=urgency_level,
                created_by_chp=chp
            )
            
            return Response({
                'message': 'Appointment booked successfully',
                'appointment_id': str(appointment.id),
                'appointment_details': {
                    'patient_name': patient.user.get_full_name(),
                    'doctor_name': doctor.user.get_full_name(),
                    'date': appointment_date,
                    'time': appointment_time,
                    'type': appointment_type,
                    'status': appointment.status,
                    'chp_name': chp.user.get_full_name()
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating appointment: {e}")
            return Response({'error': 'Failed to create appointment'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CHPBatchAppointmentBookingAPIView(APIView):
    """
    API view for Community Health Provider to book multiple appointments in batch
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Book multiple appointments in batch with smart error handling",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['appointments'],
            properties={
                'appointments': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=['patient_id', 'doctor_id', 'appointment_date', 'appointment_time'],
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid", description="Pre-generated UUID from frontend (for offline sync)", example="550e8400-e29b-41d4-a716-446655440700"),
                            'patient_id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid"),
                            'doctor_id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid"),
                            'appointment_date': openapi.Schema(type=openapi.TYPE_STRING, format="date"),
                            'appointment_time': openapi.Schema(type=openapi.TYPE_STRING),
                            'appointment_type': openapi.Schema(type=openapi.TYPE_STRING, default='routine'),
                            'notes': openapi.Schema(type=openapi.TYPE_STRING),
                            'symptoms': openapi.Schema(type=openapi.TYPE_STRING),
                            'urgency_level': openapi.Schema(type=openapi.TYPE_STRING, default='medium'),
                            'created_offline_at': openapi.Schema(type=openapi.TYPE_STRING, format="date-time", description="Timestamp when appointment was created offline", example="2025-12-17T10:30:00Z")
                        }
                    )
                )
            }
        ),
        responses={
            200: openapi.Response("Batch booking completed with results", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'diagnostic': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'status': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'partial_success', 'failed']),
                            'message': openapi.Schema(type=openapi.TYPE_STRING)
                        }
                    ),
                    'results': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'successful_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'failed_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'successful_ids': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                            'failed_items': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'id': openapi.Schema(type=openapi.TYPE_STRING),
                                        'reason': openapi.Schema(type=openapi.TYPE_STRING),
                                        'error_code': openapi.Schema(type=openapi.TYPE_STRING),
                                        'index': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'data': openapi.Schema(type=openapi.TYPE_OBJECT)
                                    }
                                )
                            )
                        }
                    ),
                    'metadata': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'total_attempts': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'success_rate': openapi.Schema(type=openapi.TYPE_STRING),
                            'processing_time': openapi.Schema(type=openapi.TYPE_STRING),
                            'error_breakdown': openapi.Schema(type=openapi.TYPE_OBJECT)
                        }
                    )
                }
            )),
            400: openapi.Response("Bad Request"),
            403: openapi.Response("Permission Denied")
        }
    )
    def post(self, request):
        # Track processing start time
        from datetime import datetime
        start_time = datetime.now().timestamp()
        
        # Check if user is a Community Health Provider
        try:
            chp = CommunityHealthProvider.objects.get(user=request.user)
        except CommunityHealthProvider.DoesNotExist:
            return Response({'error': 'Only Community Health Providers can book batch appointments'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        appointments_data = request.data.get('appointments', [])
        if not appointments_data:
            return Response({'error': 'appointments list is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        successful_bookings = []
        failed_bookings = []
        
        from healthcare.models import Appointment, HealthCare, DoctorAvailability
        from doctors.models import Doctor
        from datetime import datetime
        
        # Get default healthcare facility
        healthcare_facility = HealthCare.objects.first()
        
        for idx, appointment_data in enumerate(appointments_data):
            try:
                # Validate required fields
                required_fields = ['patient_id', 'doctor_id', 'appointment_date', 'appointment_time']
                missing_fields = [field for field in required_fields if not appointment_data.get(field)]
                
                if missing_fields:
                    failed_bookings.append({
                        'index': idx,
                        'data': appointment_data,
                        'error': f"Missing required fields: {', '.join(missing_fields)}",
                        'error_type': 'validation'
                    })
                    continue
                
                # Check if appointment with this ID already exists (for offline sync)
                appointment_id = appointment_data.get('id')
                if appointment_id:
                    try:
                        existing_appointment = Appointment.objects.get(id=appointment_id)
                        failed_bookings.append({
                            'index': idx,
                            'data': appointment_data,
                            'error': f'Appointment with ID {appointment_id} already exists',
                            'error_type': 'duplicate'
                        })
                        continue
                    except Appointment.DoesNotExist:
                        # Good, appointment doesn't exist yet
                        pass
                
                # Get models
                try:
                    patient = Patient.objects.get(id=appointment_data['patient_id'])
                except Patient.DoesNotExist:
                    failed_bookings.append({
                        'index': idx,
                        'data': appointment_data,
                        'error': 'Patient not found',
                        'error_type': 'not_found'
                    })
                    continue
                
                try:
                    doctor = Doctor.objects.get(id=appointment_data['doctor_id'])
                except Doctor.DoesNotExist:
                    failed_bookings.append({
                        'index': idx,
                        'data': appointment_data,
                        'error': 'Doctor not found',
                        'error_type': 'not_found'
                    })
                    continue
                
                # Parse date and time
                try:
                    date_obj = datetime.strptime(appointment_data['appointment_date'], '%Y-%m-%d').date()
                    time_obj = datetime.strptime(appointment_data['appointment_time'], '%H:%M').time()
                except ValueError:
                    failed_bookings.append({
                        'index': idx,
                        'data': appointment_data,
                        'error': 'Invalid date or time format',
                        'error_type': 'validation'
                    })
                    continue
                
                # Check doctor availability
                weekday = date_obj.weekday()
                availability = DoctorAvailability.objects.filter(
                    doctor=doctor,
                    weekday=weekday,
                    start_time__lte=time_obj,
                    end_time__gte=time_obj,
                    is_available=True
                ).first()
                
                if not availability:
                    failed_bookings.append({
                        'index': idx,
                        'data': appointment_data,
                        'error': 'Doctor not available at requested time',
                        'error_type': 'availability'
                    })
                    continue
                
                # Check for conflicts
                from datetime import timedelta
                end_time_obj = (datetime.combine(date_obj, time_obj) + timedelta(minutes=30)).time()
                
                existing_appointment = Appointment.objects.filter(
                    doctor=doctor,
                    appointment_date=date_obj,
                    start_time=time_obj,
                    status__in=['BOOKED', 'SCHEDULED', 'ARRIVED']
                ).exists()
                
                if existing_appointment:
                    failed_bookings.append({
                        'index': idx,
                        'data': appointment_data,
                        'error': 'Time slot already booked',
                        'error_type': 'conflict'
                    })
                    continue
                
                # Prepare appointment data
                appointment_create_data = {
                    'patient': patient,
                    'doctor': doctor,
                    'healthcare_facility': healthcare_facility,
                    'appointment_date': date_obj,
                    'start_time': time_obj,
                    'end_time': end_time_obj,
                    'appointment_type': appointment_data.get('appointment_type', 'routine'),
                    'status': 'BOOKED',
                    'notes': appointment_data.get('notes', ''),
                    'reason': appointment_data.get('symptoms', ''),
                    'risk_level': appointment_data.get('urgency_level', 'medium'),
                    'created_by_chp': chp
                }
                
                # Use pre-generated ID if provided (for offline sync)
                if appointment_id:
                    appointment_create_data['id'] = appointment_id
                
                # Handle offline creation timestamp
                created_offline_at = appointment_data.get('created_offline_at')
                if created_offline_at:
                    try:
                        from datetime import datetime
                        import pytz
                        # Parse the offline timestamp and use it as created_at
                        if isinstance(created_offline_at, str):
                            # Remove timezone info if present and parse
                            if created_offline_at.endswith('Z'):
                                created_offline_at = created_offline_at[:-1] + '+00:00'
                            offline_dt = datetime.fromisoformat(created_offline_at.replace('Z', '+00:00'))
                            if offline_dt.tzinfo is None:
                                offline_dt = pytz.UTC.localize(offline_dt)
                            appointment_create_data['created_at'] = offline_dt
                    except (ValueError, TypeError):
                        # If parsing fails, use current timestamp
                        pass
                
                # Create appointment
                appointment = Appointment.objects.create(**appointment_create_data)
                
                successful_bookings.append({
                    'index': idx,
                    'appointment_id': str(appointment.id),
                    'patient_name': patient.user.get_full_name(),
                    'doctor_name': doctor.user.get_full_name(),
                    'date': appointment_data['appointment_date'],
                    'time': appointment_data['appointment_time']
                })
                
            except Exception as e:
                failed_bookings.append({
                    'index': idx,
                    'data': appointment_data,
                    'error': f'Unexpected error: {str(e)}',
                    'error_type': 'system_error'
                })
        
        # Determine overall status
        total_attempts = len(appointments_data)
        successful_count = len(successful_bookings)
        failed_count = len(failed_bookings)
        
        if failed_count == 0:
            diagnostic_status = "success"
            diagnostic_message = f"Successfully created all {successful_count} appointments"
        elif successful_count == 0:
            diagnostic_status = "failed"
            diagnostic_message = f"Failed to create all {total_attempts} appointments"
        else:
            diagnostic_status = "partial_success"
            diagnostic_message = f"Created {successful_count} of {total_attempts} appointments"
        
        # Extract successful IDs
        successful_ids = [booking['appointment_id'] for booking in successful_bookings]
        
        # Format failed items with proper error codes
        failed_items = []
        for failed in failed_bookings:
            # Map error types to standardized error codes
            error_code_map = {
                'validation': 'INVALID_DATA',
                'not_found': 'RESOURCE_NOT_FOUND',
                'availability': 'DOCTOR_UNAVAILABLE',
                'conflict': 'TIME_SLOT_CONFLICT',
                'duplicate': 'DUPLICATE_APPOINTMENT_ID',
                'system_error': 'SYSTEM_ERROR'
            }
            
            # Create unique identifier for failed item (use index or patient_id if available)
            item_id = failed['data'].get('patient_id', f"item_{failed['index']}")
            error_code = error_code_map.get(failed['error_type'], 'UNKNOWN_ERROR')
            
            failed_items.append({
                'id': item_id,
                'reason': failed['error'],
                'error_code': error_code,
                'index': failed['index'],  # Keep index for reference
                'data': failed['data']      # Include original data for debugging
            })
        
        response_data = {
            'diagnostic': {
                'status': diagnostic_status,
                'message': diagnostic_message
            },
            'results': {
                'successful_count': successful_count,
                'failed_count': failed_count,
                'successful_ids': successful_ids,
                'failed_items': failed_items
            }
        }
        
        # Add additional metadata for debugging/analytics
        response_data['metadata'] = {
            'total_attempts': total_attempts,
            'success_rate': f"{(successful_count / total_attempts) * 100:.1f}%" if total_attempts > 0 else "0%",
            'error_breakdown': {
                'validation_errors': len([f for f in failed_bookings if f['error_type'] == 'validation']),
                'not_found_errors': len([f for f in failed_bookings if f['error_type'] == 'not_found']),
                'availability_errors': len([f for f in failed_bookings if f['error_type'] == 'availability']),
                'conflict_errors': len([f for f in failed_bookings if f['error_type'] == 'conflict']),
                'system_errors': len([f for f in failed_bookings if f['error_type'] == 'system_error'])
            },
            'processing_time': f"{(datetime.now().timestamp() - start_time):.2f}s" if 'start_time' in locals() else None
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class CHPPatientAppointmentsAPIView(APIView):
    """
    API view for Community Health Provider to view appointments they created for patients
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="View all appointments created by the Community Health Provider with comprehensive filtering options. Returns appointment details including patient info, doctor info, and healthcare facility details.",
        manual_parameters=[
            openapi.Parameter('patient_id', openapi.IN_QUERY, description="Filter by specific patient UUID", type=openapi.TYPE_STRING, format="uuid", example="550e8400-e29b-41d4-a716-446655440300"),
            openapi.Parameter('status', openapi.IN_QUERY, description="Filter by appointment status", type=openapi.TYPE_STRING, enum=['BOOKED', 'SCHEDULED', 'ARRIVED', 'FULFILLED', 'CANCELLED', 'NOSHOW'], example="BOOKED"),
            openapi.Parameter('date_from', openapi.IN_QUERY, description="Start date filter (YYYY-MM-DD)", type=openapi.TYPE_STRING, format="date", example="2025-12-01"),
            openapi.Parameter('date_to', openapi.IN_QUERY, description="End date filter (YYYY-MM-DD)", type=openapi.TYPE_STRING, format="date", example="2025-12-31"),
            openapi.Parameter('doctor_id', openapi.IN_QUERY, description="Filter by specific doctor UUID", type=openapi.TYPE_STRING, format="uuid", example="550e8400-e29b-41d4-a716-446655440600")
        ],
        responses={
            200: openapi.Response("List of appointments", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER, example=3),
                    'appointments': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid"),
                                'patient': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid"),
                                        'name': openapi.Schema(type=openapi.TYPE_STRING, example="Mary Wanjiku"),
                                        'email': openapi.Schema(type=openapi.TYPE_STRING, example="patient@example.com")
                                    }
                                ),
                                'doctor': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid"),
                                        'name': openapi.Schema(type=openapi.TYPE_STRING, example="Dr. John Smith"),
                                        'specialty': openapi.Schema(type=openapi.TYPE_STRING, example="Cardiology")
                                    }
                                ),
                                'appointment_date': openapi.Schema(type=openapi.TYPE_STRING, format="date", example="2025-12-20"),
                                'start_time': openapi.Schema(type=openapi.TYPE_STRING, example="14:30"),
                                'end_time': openapi.Schema(type=openapi.TYPE_STRING, example="15:00"),
                                'appointment_type': openapi.Schema(type=openapi.TYPE_STRING, example="consultation"),
                                'status': openapi.Schema(type=openapi.TYPE_STRING, example="BOOKED"),
                                'notes': openapi.Schema(type=openapi.TYPE_STRING, example="Follow-up appointment"),
                                'reason': openapi.Schema(type=openapi.TYPE_STRING, example="Persistent headache"),
                                'risk_level': openapi.Schema(type=openapi.TYPE_STRING, example="medium"),
                                'created_at': openapi.Schema(type=openapi.TYPE_STRING, format="date-time"),
                                'healthcare_facility': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'name': openapi.Schema(type=openapi.TYPE_STRING, example="Nairobi General Hospital"),
                                        'location': openapi.Schema(type=openapi.TYPE_STRING, example="123 Hospital Avenue, Nairobi")
                                    }
                                )
                            }
                        )
                    ),
                    'chp_info': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid"),
                            'name': openapi.Schema(type=openapi.TYPE_STRING, example="Nurse Jane Doe"),
                            'specialization': openapi.Schema(type=openapi.TYPE_STRING, example="Community Health"),
                            'service_area': openapi.Schema(type=openapi.TYPE_STRING, example="Westlands District")
                        }
                    )
                }
            )),
            400: openapi.Response("Bad Request", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'error': openapi.Schema(type=openapi.TYPE_STRING, example="Invalid date_from format. Use YYYY-MM-DD")}
            )),
            403: openapi.Response("Permission Denied", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'error': openapi.Schema(type=openapi.TYPE_STRING, example="Only Community Health Providers can view their appointments")}
            ))
        },
        tags=['Community Health Provider']
    )
    def get(self, request):
        # Check if user is a Community Health Provider
        try:
            chp = CommunityHealthProvider.objects.get(user=request.user)
        except CommunityHealthProvider.DoesNotExist:
            return Response({'error': 'Only Community Health Providers can view their appointments'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        from healthcare.models import Appointment
        from datetime import datetime
        
        # Base query for appointments created by this CHP
        appointments_query = Appointment.objects.filter(created_by_chp=chp)
        
        # Apply filters
        patient_id = request.query_params.get('patient_id')
        if patient_id:
            appointments_query = appointments_query.filter(patient_id=patient_id)
        
        status_filter = request.query_params.get('status')
        if status_filter:
            appointments_query = appointments_query.filter(status__iexact=status_filter)
        
        doctor_id = request.query_params.get('doctor_id')
        if doctor_id:
            appointments_query = appointments_query.filter(doctor_id=doctor_id)
        
        date_from = request.query_params.get('date_from')
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                appointments_query = appointments_query.filter(appointment_date__gte=date_from_obj)
            except ValueError:
                return Response({'error': 'Invalid date_from format. Use YYYY-MM-DD'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        
        date_to = request.query_params.get('date_to')
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                appointments_query = appointments_query.filter(appointment_date__lte=date_to_obj)
            except ValueError:
                return Response({'error': 'Invalid date_to format. Use YYYY-MM-DD'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        
        # Order by most recent first
        appointments = appointments_query.order_by('-appointment_date', '-start_time')
        
        # Prepare response data
        appointments_data = []
        for appointment in appointments:
            appointments_data.append({
                'id': str(appointment.id),
                'patient': {
                    'id': str(appointment.patient.id),
                    'name': appointment.patient.user.get_full_name(),
                    'email': appointment.patient.user.email
                },
                'doctor': {
                    'id': str(appointment.doctor.id),
                    'name': appointment.doctor.user.get_full_name(),
                    'specialty': appointment.doctor.specialty
                },
                'appointment_date': appointment.appointment_date.strftime('%Y-%m-%d'),
                'start_time': appointment.start_time.strftime('%H:%M'),
                'end_time': appointment.end_time.strftime('%H:%M'),
                'appointment_type': appointment.appointment_type,
                'status': appointment.status,
                'notes': appointment.notes,
                'reason': appointment.reason,
                'risk_level': appointment.risk_level,
                'created_at': appointment.created_at.isoformat(),
                'healthcare_facility': {
                    'name': appointment.healthcare_facility.name if appointment.healthcare_facility else 'Not specified',
                    'location': appointment.healthcare_facility.address if appointment.healthcare_facility else 'Not specified'
                }
            })
        
        return Response({
            'count': len(appointments_data),
            'appointments': appointments_data,
            'chp_info': {
                'id': str(chp.id),
                'name': chp.user.get_full_name(),
                'specialization': chp.specialization,
                'service_area': chp.service_area
            }
        }, status=status.HTTP_200_OK)


class CHPPatientsListAPIView(APIView):
    """
    API view for Community Health Provider to view all patients they have onboarded
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get all patients that the authenticated Community Health Provider has onboarded/created. Includes comprehensive patient information, medical details, and appointment statistics.",
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Search by patient name or email", type=openapi.TYPE_STRING, example="Mary"),
            openapi.Parameter('location_id', openapi.IN_QUERY, description="Filter by patient location UUID", type=openapi.TYPE_STRING, format="uuid", example="550e8400-e29b-41d4-a716-446655440030"),
            openapi.Parameter('is_active', openapi.IN_QUERY, description="Filter by patient active status", type=openapi.TYPE_BOOLEAN, example=True),
            openapi.Parameter('date_from', openapi.IN_QUERY, description="Filter by onboarding date from (YYYY-MM-DD)", type=openapi.TYPE_STRING, format="date", example="2025-12-01"),
            openapi.Parameter('date_to', openapi.IN_QUERY, description="Filter by onboarding date to (YYYY-MM-DD)", type=openapi.TYPE_STRING, format="date", example="2025-12-31"),
            openapi.Parameter('blood_type', openapi.IN_QUERY, description="Filter by blood type", type=openapi.TYPE_STRING, enum=['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'], example="O+"),
            openapi.Parameter('gender', openapi.IN_QUERY, description="Filter by gender", type=openapi.TYPE_STRING, enum=['male', 'female', 'other', 'unknown'], example="female")
        ],
        responses={
            200: openapi.Response("List of CHP's onboarded patients", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER, example=5),
                    'patients': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid"),
                                'name': openapi.Schema(type=openapi.TYPE_STRING, example="Mary Wanjiku"),
                                'email': openapi.Schema(type=openapi.TYPE_STRING, example="patient@example.com"),
                                'phone': openapi.Schema(type=openapi.TYPE_STRING, example="+254722333444"),
                                'date_of_birth': openapi.Schema(type=openapi.TYPE_STRING, format="date", example="1985-03-15"),
                                'age': openapi.Schema(type=openapi.TYPE_INTEGER, example=39),
                                'gender': openapi.Schema(type=openapi.TYPE_STRING, example="female"),
                                'blood_type': openapi.Schema(type=openapi.TYPE_STRING, example="O+"),
                                'location': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid"),
                                        'name': openapi.Schema(type=openapi.TYPE_STRING, example="Parklands Estate"),
                                        'level': openapi.Schema(type=openapi.TYPE_STRING, example="village")
                                    }
                                ),
                                'medical_info': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'allergies': openapi.Schema(type=openapi.TYPE_STRING, example="Penicillin"),
                                        'medical_conditions': openapi.Schema(type=openapi.TYPE_STRING, example="Diabetes Type 2"),
                                        'current_medications': openapi.Schema(type=openapi.TYPE_STRING, example="Metformin 500mg"),
                                        'height_cm': openapi.Schema(type=openapi.TYPE_INTEGER, example=165),
                                        'weight_kg': openapi.Schema(type=openapi.TYPE_STRING, example="65.50")
                                    }
                                ),
                                'emergency_contact': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'name': openapi.Schema(type=openapi.TYPE_STRING, example="John Wanjiku"),
                                        'phone': openapi.Schema(type=openapi.TYPE_STRING, example="+254722555666"),
                                        'relationship': openapi.Schema(type=openapi.TYPE_STRING, example="Spouse")
                                    }
                                ),
                                'onboarded_at': openapi.Schema(type=openapi.TYPE_STRING, format="date-time"),
                                'appointment_stats': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'total_appointments': openapi.Schema(type=openapi.TYPE_INTEGER, example=3),
                                        'upcoming_appointments': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                        'last_appointment_date': openapi.Schema(type=openapi.TYPE_STRING, format="date", example="2025-12-20"),
                                        'next_appointment_date': openapi.Schema(type=openapi.TYPE_STRING, format="date", example="2025-12-25")
                                    }
                                ),
                                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True)
                            }
                        )
                    ),
                    'chp_info': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_STRING, format="uuid"),
                            'name': openapi.Schema(type=openapi.TYPE_STRING, example="Nurse Jane Doe"),
                            'specialization': openapi.Schema(type=openapi.TYPE_STRING, example="Community Health"),
                            'service_area': openapi.Schema(type=openapi.TYPE_STRING, example="Westlands District"),
                            'total_patients_onboarded': openapi.Schema(type=openapi.TYPE_INTEGER, example=5)
                        }
                    )
                }
            )),
            400: openapi.Response("Bad Request", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'error': openapi.Schema(type=openapi.TYPE_STRING, example="Invalid date format. Use YYYY-MM-DD")}
            )),
            403: openapi.Response("Permission Denied", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'error': openapi.Schema(type=openapi.TYPE_STRING, example="Only Community Health Providers can view their patients")}
            ))
        },
        tags=['Community Health Provider']
    )
    def get(self, request):
        # Check if user is a Community Health Provider
        try:
            chp = CommunityHealthProvider.objects.get(user=request.user)
        except CommunityHealthProvider.DoesNotExist:
            return Response({'error': 'Only Community Health Providers can view their patients'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        from datetime import datetime, date
        from django.db.models import Q, Count
        
        # Base query for patients created by this CHP
        patients_query = Patient.objects.filter(created_by_chp=chp).select_related('user', 'user__location')
        
        # Apply filters
        search = request.query_params.get('search')
        if search:
            patients_query = patients_query.filter(
                Q(user__first_name__icontains=search) | 
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search)
            )
        
        location_id = request.query_params.get('location_id')
        if location_id:
            patients_query = patients_query.filter(user__location_id=location_id)
        
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() in ['true', '1', 'yes']
            patients_query = patients_query.filter(active=is_active_bool)
        
        blood_type = request.query_params.get('blood_type')
        if blood_type:
            patients_query = patients_query.filter(blood_type=blood_type)
        
        gender = request.query_params.get('gender')
        if gender:
            patients_query = patients_query.filter(gender=gender)
        
        # Date filters
        date_from = request.query_params.get('date_from')
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                patients_query = patients_query.filter(created_at__date__gte=date_from_obj)
            except ValueError:
                return Response({'error': 'Invalid date_from format. Use YYYY-MM-DD'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        
        date_to = request.query_params.get('date_to')
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                patients_query = patients_query.filter(created_at__date__lte=date_to_obj)
            except ValueError:
                return Response({'error': 'Invalid date_to format. Use YYYY-MM-DD'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        
        patients = patients_query.distinct()
        
        # Prepare response data
        patients_data = []
        for patient in patients:
            # Calculate age if date_of_birth is available
            age = None
            if patient.date_of_birth:
                today = date.today()
                age = today.year - patient.date_of_birth.year - ((today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day))
            
            # Get appointment statistics
            from healthcare.models import Appointment
            from django.utils import timezone
            
            total_appointments = Appointment.objects.filter(patient=patient, created_by_chp=chp).count()
            upcoming_appointments = Appointment.objects.filter(
                patient=patient, 
                created_by_chp=chp,
                appointment_date__gte=timezone.now().date(),
                status__in=['BOOKED', 'SCHEDULED', 'ARRIVED']
            ).count()
            
            # Last appointment
            last_appointment = Appointment.objects.filter(
                patient=patient,
                created_by_chp=chp
            ).order_by('-appointment_date', '-start_time').first()
            
            # Next appointment
            next_appointment = Appointment.objects.filter(
                patient=patient,
                created_by_chp=chp,
                appointment_date__gte=timezone.now().date(),
                status__in=['BOOKED', 'SCHEDULED', 'ARRIVED']
            ).order_by('appointment_date', 'start_time').first()
            
            patient_data = {
                'id': str(patient.id),
                'name': patient.user.get_full_name(),
                'email': patient.user.email,
                'phone': patient.user.phone_number,
                'date_of_birth': patient.date_of_birth.isoformat() if patient.date_of_birth else None,
                'age': age,
                'gender': patient.gender,
                'blood_type': patient.blood_type,
                'location': None,
                'medical_info': {
                    'allergies': patient.allergies,
                    'medical_conditions': patient.medical_conditions,
                    'current_medications': patient.medications,
                    'height_cm': patient.height_cm,
                    'weight_kg': str(patient.weight_kg) if patient.weight_kg else None
                },
                'emergency_contact': {
                    'name': patient.emergency_contact_name,
                    'phone': patient.emergency_contact_phone,
                    'relationship': patient.emergency_contact_relationship
                },
                'onboarded_at': patient.created_at.isoformat(),
                'appointment_stats': {
                    'total_appointments': total_appointments,
                    'upcoming_appointments': upcoming_appointments,
                    'last_appointment_date': last_appointment.appointment_date.isoformat() if last_appointment else None,
                    'next_appointment_date': next_appointment.appointment_date.isoformat() if next_appointment else None
                },
                'is_active': patient.active
            }
            
            # Add location info if available
            if patient.user.location:
                patient_data['location'] = {
                    'id': str(patient.user.location.id),
                    'name': patient.user.location.name,
                    'level': patient.user.location.level
                }
            
            patients_data.append(patient_data)
        
        return Response({
            'count': len(patients_data),
            'patients': patients_data,
            'chp_info': {
                'id': str(chp.id),
                'name': chp.user.get_full_name(),
                'specialization': chp.specialization,
                'service_area': chp.service_area,
                'total_patients_onboarded': len(patients_data)
            }
        }, status=status.HTTP_200_OK)


class CHPStatsAPIView(APIView):
    """
    Get statistics for Community Health Provider including:
    - Number of referrals (appointments created by CHP)
    - Average rating of doctors CHP referred patients to
    - Joining date
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from healthcare.models import Appointment, DoctorRating
        from django.db.models import Avg
        
        try:
            # Get the CHP profile
            chp = CommunityHealthProvider.objects.get(user=request.user)
        except CommunityHealthProvider.DoesNotExist:
            return Response({
                'error': 'CHP profile not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Count referrals (appointments created by this CHP)
        referrals_count = Appointment.objects.filter(created_by_chp=chp).count()

        # Get all doctors that this CHP has referred patients to
        referred_doctors = Appointment.objects.filter(
            created_by_chp=chp
        ).values_list('doctor', flat=True).distinct()

        # Calculate average rating of those doctors
        average_rating = None
        if referred_doctors:
            ratings = DoctorRating.objects.filter(
                doctor__in=referred_doctors
            ).aggregate(avg_rating=Avg('rating'))
            average_rating = round(ratings['avg_rating'], 2) if ratings['avg_rating'] else None

        # Get joining date
        joining_date = chp.user.date_joined

        return Response({
            'chp_id': str(chp.id),
            'chp_name': chp.user.get_full_name(),
            'stats': {
                'referrals_count': referrals_count,
                'average_rating': average_rating,
                'joining_date': joining_date.isoformat()
            }
        }, status=status.HTTP_200_OK)


class CHPProfileAPIView(APIView):
    """
    Get CHP profile by UUID
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, chp_id):
        try:
            chp = CommunityHealthProvider.objects.get(id=chp_id)
        except CommunityHealthProvider.DoesNotExist:
            return Response({
                'error': 'CHP not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Build profile response
        profile_data = {
            'id': str(chp.id),
            'user': {
                'id': str(chp.user.id),
                'username': chp.user.username,
                'first_name': chp.user.first_name,
                'last_name': chp.user.last_name,
                'email': chp.user.email,
                'phone': chp.user.phone_number,
                'date_joined': chp.user.date_joined.isoformat(),
                'is_active': chp.user.is_active,
                'is_verified': chp.user.is_verified
            },
            'certification_number': chp.certification_number,
            'years_of_experience': chp.years_of_experience,
            'specialization': chp.specialization,
            'service_area': chp.service_area,
            'languages': chp.languages_spoken,
            'is_active': chp.is_active,
            'created_at': chp.created_at.isoformat(),
            'updated_at': chp.updated_at.isoformat()
        }

        # Add location info if available
        if chp.user.location:
            profile_data['user']['location'] = {
                'id': str(chp.user.location.id),
                'name': chp.user.location.name,
                'level': chp.user.location.level
            }

        return Response(profile_data, status=status.HTTP_200_OK)


class AdminCHPAssignmentAPIView(APIView):
    """
    Admin endpoint to assign/reassign CHP to patient
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Check if user is admin
        if not request.user.roles.filter(name='admin').exists():
            return Response({
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = CHPAssignmentSerializer(data=request.data)
        if serializer.is_valid():
            chp_id = serializer.validated_data['chp_id']
            patient_id = serializer.validated_data['patient_id']
            
            try:
                chp = CommunityHealthProvider.objects.get(id=chp_id)
                patient = Patient.objects.get(id=patient_id)
                
                # Get previous CHP if any
                previous_chp = patient.created_by_chp
                
                # Assign CHP to patient
                patient.created_by_chp = chp
                patient.save()
                
                # Create audit log
                AuditLog.objects.create(
                    user=request.user,
                    username=request.user.username,
                    activity='chp_assignment',
                    email_address=request.user.email,
                    role=','.join([role.name for role in request.user.roles.all()]),
                    date_joined=request.user.date_joined,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    details={
                        'patient_id': str(patient.id),
                        'patient_name': patient.user.get_full_name(),
                        'chp_id': str(chp.id),
                        'chp_name': chp.user.get_full_name(),
                        'previous_chp_id': str(previous_chp.id) if previous_chp else None,
                        'previous_chp_name': previous_chp.user.get_full_name() if previous_chp else None,
                        'action': 'reassignment' if previous_chp else 'assignment'
                    }
                )
                
                return Response({
                    'message': f"Patient {patient.user.get_full_name()} successfully {'reassigned' if previous_chp else 'assigned'} to CHP {chp.user.get_full_name()}",
                    'patient': {
                        'id': str(patient.id),
                        'name': patient.user.get_full_name(),
                        'email': patient.user.email
                    },
                    'chp': {
                        'id': str(chp.id),
                        'name': chp.user.get_full_name(),
                        'specialization': chp.specialization
                    },
                    'previous_chp': {
                        'id': str(previous_chp.id),
                        'name': previous_chp.user.get_full_name()
                    } if previous_chp else None
                }, status=status.HTTP_200_OK)
                
            except CommunityHealthProvider.DoesNotExist:
                return Response({
                    'error': 'CHP not found'
                }, status=status.HTTP_404_NOT_FOUND)
            except Patient.DoesNotExist:
                return Response({
                    'error': 'Patient not found'
                }, status=status.HTTP_404_NOT_FOUND)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CHPPatientMessageAPIView(APIView):
    """
    Endpoint for CHP-Patient messaging
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get messages for current user (either CHP or Patient)"""
        user = request.user
        patient_id = request.query_params.get('patient_id')
        chp_id = request.query_params.get('chp_id')
        
        # Check if user is CHP or patient
        is_chp = user.roles.filter(name__in=['chp', 'community_health_provider']).exists()
        is_patient = user.roles.filter(name='patient').exists()
        
        if not (is_chp or is_patient):
            return Response({
                'error': 'Only CHPs and patients can access messages'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Build query based on user type
        if is_chp:
            if patient_id:
                # CHP viewing messages with specific patient
                messages = CHPPatientMessage.objects.filter(
                    Q(sender=user, patient_id=patient_id) |
                    Q(recipient=user, patient_id=patient_id)
                )
            else:
                # CHP viewing all their messages
                messages = CHPPatientMessage.objects.filter(
                    Q(sender=user) | Q(recipient=user)
                )
        else:  # is_patient
            # Patient viewing their messages with CHP
            try:
                patient = Patient.objects.get(user=user)
                if chp_id:
                    messages = CHPPatientMessage.objects.filter(
                        patient=patient,
                        chp_id=chp_id
                    )
                else:
                    messages = CHPPatientMessage.objects.filter(patient=patient)
            except Patient.DoesNotExist:
                return Response({
                    'error': 'Patient profile not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = CHPPatientMessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Send a message"""
        user = request.user
        data = request.data.copy()
        
        # Set sender
        data['sender'] = user.id
        
        # Validate sender is either CHP or patient
        is_chp = user.roles.filter(name__in=['chp', 'community_health_provider']).exists()
        is_patient = user.roles.filter(name='patient').exists()
        
        if not (is_chp or is_patient):
            return Response({
                'error': 'Only CHPs and patients can send messages'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = CHPPatientMessageSerializer(data=data)
        if serializer.is_valid():
            # Additional validation
            patient_id = serializer.validated_data['patient']
            chp_id = serializer.validated_data['chp']
            recipient_id = serializer.validated_data['recipient']
            
            try:
                patient = Patient.objects.get(id=patient_id.id)
                chp = CommunityHealthProvider.objects.get(id=chp_id.id)
                recipient = User.objects.get(id=recipient_id.id)
                
                # Ensure the relationship is valid
                if is_chp:
                    # CHP sending to patient
                    if patient.user != recipient:
                        return Response({
                            'error': 'Recipient must be the patient'
                        }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # Patient sending to CHP
                    if chp.user != recipient:
                        return Response({
                            'error': 'Recipient must be the assigned CHP'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    if patient.user != user:
                        return Response({
                            'error': 'You can only send messages for your own patient profile'
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                message = serializer.save()
                return Response(CHPPatientMessageSerializer(message).data, status=status.HTTP_201_CREATED)
                
            except (Patient.DoesNotExist, CommunityHealthProvider.DoesNotExist, User.DoesNotExist) as e:
                return Response({
                    'error': 'Invalid patient, CHP, or recipient'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, message_id):
        """Mark message as read"""
        try:
            message = CHPPatientMessage.objects.get(id=message_id, recipient=request.user)
            message.is_read = True
            message.save()
            
            return Response({
                'message': 'Message marked as read'
            }, status=status.HTTP_200_OK)
            
        except CHPPatientMessage.DoesNotExist:
            return Response({
                'error': 'Message not found'
            }, status=status.HTTP_404_NOT_FOUND)


class CHPReferralCreateAPIView(APIView):
    """
    CHP endpoint to create patient referrals to doctors
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Create a new patient referral"""
        try:
            # Verify user is a CHP
            chp = request.user.community_health_provider
        except CommunityHealthProvider.DoesNotExist:
            return Response({
                'error': 'You must be a Community Health Provider to create referrals'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ReferralCreateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            referral = serializer.save()
            
            return Response({
                'message': 'Referral created successfully',
                'referral_id': referral.id,
                'patient': referral.patient.user.get_full_name(),
                'doctor': f"Dr. {referral.referred_to_doctor.user.get_full_name()}",
                'status': referral.status,
                'created_at': referral.created_at
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CHPReferralsListAPIView(APIView):
    """
    CHP endpoint to list all patients referred by the CHP
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """List all referrals made by the authenticated CHP"""
        try:
            # Verify user is a CHP
            chp = request.user.community_health_provider
        except CommunityHealthProvider.DoesNotExist:
            return Response({
                'error': 'You must be a Community Health Provider to view referrals'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get all referrals made by this CHP
        referrals = Referral.objects.filter(referring_chp=chp)
        
        # Apply filters
        status_filter = request.GET.get('status', None)
        if status_filter:
            referrals = referrals.filter(status=status_filter)
        
        urgency_filter = request.GET.get('urgency', None)
        if urgency_filter:
            referrals = referrals.filter(urgency=urgency_filter)
        
        patient_search = request.GET.get('patient_search', None)
        if patient_search:
            referrals = referrals.filter(
                Q(patient__user__first_name__icontains=patient_search) |
                Q(patient__user__last_name__icontains=patient_search) |
                Q(patient__user__email__icontains=patient_search)
            )
        
        doctor_search = request.GET.get('doctor_search', None)
        if doctor_search:
            referrals = referrals.filter(
                Q(referred_to_doctor__user__first_name__icontains=doctor_search) |
                Q(referred_to_doctor__user__last_name__icontains=doctor_search) |
                Q(referred_to_doctor__specialty__icontains=doctor_search)
            )
        
        # Order by creation date (newest first)
        referrals = referrals.order_by('-created_at')
        
        # Paginate results
        from django.core.paginator import Paginator
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        paginator = Paginator(referrals, page_size)
        page_obj = paginator.get_page(page)
        
        serializer = ReferralListSerializer(page_obj, many=True)
        
        # Prepare summary statistics
        total_referrals = referrals.count()
        pending_count = referrals.filter(status='pending').count()
        accepted_count = referrals.filter(status='accepted').count()
        completed_count = referrals.filter(status='completed').count()
        
        return Response({
            'referrals': serializer.data,
            'pagination': {
                'current_page': page,
                'total_pages': paginator.num_pages,
                'total_results': total_referrals,
                'page_size': page_size,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            },
            'summary': {
                'total_referrals': total_referrals,
                'pending': pending_count,
                'accepted': accepted_count,
                'completed': completed_count
            }
        }, status=status.HTTP_200_OK)


class CHPReferralDetailAPIView(APIView):
    """
    CHP endpoint to view details of a specific referral
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, referral_id):
        """Get detailed information about a specific referral"""
        try:
            # Verify user is a CHP
            chp = request.user.community_health_provider
        except CommunityHealthProvider.DoesNotExist:
            return Response({
                'error': 'You must be a Community Health Provider to view referrals'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Get the referral and ensure it belongs to this CHP
            referral = Referral.objects.get(id=referral_id, referring_chp=chp)
        except Referral.DoesNotExist:
            return Response({
                'error': 'Referral not found or you do not have permission to view it'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ReferralDetailSerializer(referral)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request, referral_id):
        """Update referral status or add notes (limited fields)"""
        try:
            # Verify user is a CHP
            chp = request.user.community_health_provider
        except CommunityHealthProvider.DoesNotExist:
            return Response({
                'error': 'You must be a Community Health Provider to update referrals'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Get the referral and ensure it belongs to this CHP
            referral = Referral.objects.get(id=referral_id, referring_chp=chp)
        except Referral.DoesNotExist:
            return Response({
                'error': 'Referral not found or you do not have permission to update it'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Only allow updating certain fields by CHP
        allowed_fields = ['clinical_notes', 'follow_up_notes', 'follow_up_required']
        update_data = {k: v for k, v in request.data.items() if k in allowed_fields}
        
        if not update_data:
            return Response({
                'error': 'No valid fields to update'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update the referral
        for field, value in update_data.items():
            setattr(referral, field, value)
        
        referral.save()
        
        serializer = ReferralDetailSerializer(referral)
        return Response({
            'message': 'Referral updated successfully',
            'referral': serializer.data
        }, status=status.HTTP_200_OK)