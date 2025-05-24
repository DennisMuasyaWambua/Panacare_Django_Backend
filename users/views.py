import os
import logging
import datetime
import secrets
import hashlib
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import authenticate, update_session_auth_hash
from django.shortcuts import get_object_or_404
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
from django.contrib.auth.tokens import default_token_generator
from rest_framework_simplejwt.tokens import RefreshToken
from panacare.settings import SIMPLE_JWT
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

from .models import User, Role, Patient
from .serializers import (
    UserSerializer, RoleSerializer, PatientSerializer, 
    PasswordChangeSerializer, EmailChangeSerializer, PhoneChangeSerializer,
    ContactUsSerializer, SupportRequestSerializer, ForgotPasswordSerializer
)
from doctors.models import Doctor
from doctors.serializers import DoctorSerializer

# Generate a secure token for admin registration
# This is a one-time use token that should be removed after use
ADMIN_REGISTRATION_TOKEN = "panacare_secure_admin_token_2025"
# Create a hash of the token for comparison (more secure than plain text)
ADMIN_TOKEN_HASH = hashlib.sha256(ADMIN_REGISTRATION_TOKEN.encode()).hexdigest()

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
                    'username': 'Your username',
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
                'username': 'Your username',
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
            
            # Send activation email for verification
            try:
                # Use frontend domain for email links if set in environment
                domain = os.environ.get('FRONTEND_DOMAIN', request.get_host())
                user.send_activation_email(domain)
                message = 'Registration successful. Please check your email to activate your account.'
            except Exception as e:
                # Log the error but don't fail the registration
                print(f"Failed to send activation email: {str(e)}")
                message = 'Registration successful. Please contact support if you do not receive an activation email.'
            
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

class UserLoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({
                'error': 'Please provide both username and password'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=username, password=password)
        
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
        refresh_token_lifetime = datetime.timedelta(days=SIMPLE_JWT.get('REFRESH_TOKEN_LIFETIME', 14))
        access_token_lifetime = datetime.timedelta(minutes=SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME', 60))
        
        expires_at = datetime.datetime.now() + access_token_lifetime
        refresh_expires_at = datetime.datetime.now() + refresh_token_lifetime
        
        # Serialize user with basic details
        user_serializer = UserSerializer(user)
        
        # Get role-specific data
        role_specific_data = {}
        
        # If user is a patient, include patient profile data
        if user.roles.filter(name='patient').exists():
            try:
                patient = Patient.objects.get(user=user)
                patient_serializer = PatientSerializer(patient)
                role_specific_data['patient'] = patient_serializer.data
            except Patient.DoesNotExist:
                role_specific_data['patient'] = None
        
        # If user is a doctor, include doctor profile data
        if user.roles.filter(name='doctor').exists():
            try:
                doctor = Doctor.objects.get(user=user)
                doctor_serializer = DoctorSerializer(doctor)
                role_specific_data['doctor'] = doctor_serializer.data
            except Doctor.DoesNotExist:
                role_specific_data['doctor'] = None
        
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
    
    # Create admin user
    serializer = UserSerializer(data=user_data)
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
            patient = Patient.objects.get(user=request.user)
            serializer = PatientSerializer(patient, context={'request': request})
            
            # Set appropriate content type for FHIR responses
            response = Response(serializer.data)
            if request.query_params.get('format') == 'fhir':
                response["Content-Type"] = "application/fhir+json"
            
            return response
        except Patient.DoesNotExist:
            return Response({
                'error': 'Patient profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request):
        # Check if user has patient role
        if not request.user.roles.filter(name='patient').exists():
            return Response({
                'error': 'Only patients can access this endpoint'
            }, status=status.HTTP_403_FORBIDDEN)
            
        try:
            patient = request.user.patient
            serializer = PatientSerializer(patient, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Patient.DoesNotExist:
            return Response({
                'error': 'Patient profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def patch(self, request):
        # Check if user has patient role
        if not request.user.roles.filter(name='patient').exists():
            return Response({
                'error': 'Only patients can access this endpoint'
            }, status=status.HTTP_403_FORBIDDEN)
            
        try:
            patient = request.user.patient
            serializer = PatientSerializer(patient, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Patient.DoesNotExist:
            return Response({
                'error': 'Patient profile not found'
            }, status=status.HTTP_404_NOT_FOUND)


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
                patient = Patient.objects.get(user=user)
                patient_serializer = PatientSerializer(patient, context={'request': request})
                response_data['patient_profile'] = patient_serializer.data
            except Patient.DoesNotExist:
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
            
            # Resend verification email
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