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
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from rest_framework_simplejwt.tokens import RefreshToken
from panacare.settings import SIMPLE_JWT

from .models import User, Role, Patient
from .serializers import UserSerializer, RoleSerializer, PatientSerializer

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
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    
    def get(self, request, format=None):
        """Provide form fields for login"""
        return Response({
            'form_fields': {
                'email': 'Your email address',
                'password': 'Your password'
            }
        })
    
    def post(self, request, format=None):
        email = request.data.get('email')
        password = request.data.get('password')
        
        # Log the request for debugging
        logger = logging.getLogger(__name__)
        logger.info(f"Login attempt for email: {email}")
        
        if not email or not password:
            return Response({
                'error': 'Please provide both email and password.',
                'form_fields': {
                    'email': 'Your email address',
                    'password': 'Your password'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=email, password=password)
        
        if user:
            if not user.is_verified:
                return Response({
                    'error': 'Please activate your account before logging in.'
                }, status=status.HTTP_401_UNAUTHORIZED)
                
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            
            # Get user roles to include in response
            roles = [role.name for role in user.roles.all()]
            
            serializer = UserSerializer(user)
            response_data = {
                'user': serializer.data,
                'roles': roles,
                'tokens': {
                    'refresh': str(refresh),
                    'access': access_token,
                },
                'auth_header_example': f'Bearer {access_token}'
            }
            
            # Add debugging info for frontend developers
            response_data['_debug'] = {
                'token_expiry': (datetime.datetime.now() + SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']).isoformat(),
                'token_length': len(access_token),
                'user_id': str(user.id),
                'username': user.username,
                'email': user.email,
            }
            
            # Log success
            logger.info(f"Login successful for user {user.email} with roles {roles}")
            
            # Set up the response
            response = Response(response_data)
            
            return response
            
        # Log failed login
        logger.warning(f"Failed login attempt for email: {email}")
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

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

class PatientListAPIView(APIView):
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="List all patients",
        manual_parameters=[format_parameter]
    )
    def get(self, request):
        patients = Patient.objects.all()
        serializer = PatientSerializer(patients, many=True, context={'request': request})
        
        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        if request.query_params.get('format') == 'fhir':
            response["Content-Type"] = "application/fhir+json"
            
        return response
    
    def post(self, request):
        serializer = PatientSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PatientDetailAPIView(APIView):
    permission_classes = [IsAdminOrAuthenticated]
    
    def get_object(self, pk):
        return get_object_or_404(Patient, pk=pk)
    
    @swagger_auto_schema(
        operation_description="Get details of a specific patient",
        manual_parameters=[format_parameter]
    )
    def get(self, request, pk):
        patient = self.get_object(pk)
        serializer = PatientSerializer(patient, context={'request': request})
        
        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        if request.query_params.get('format') == 'fhir':
            response["Content-Type"] = "application/fhir+json"
        
        return response
    
    def put(self, request, pk):
        patient = self.get_object(pk)
        serializer = PatientSerializer(patient, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        patient = self.get_object(pk)
        patient.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_admin_user(request):
    """
    Special endpoint to register an admin user. 
    This endpoint should be removed after creating the admin user.
    
    Requires a security token in the request for authorization.
    """
    logger = logging.getLogger(__name__)
    logger.info("Admin registration attempt")
    
    # Check if security token is valid
    provided_token = request.data.get('security_token', '')
    token_hash = hashlib.sha256(provided_token.encode()).hexdigest()
    
    if token_hash != ADMIN_TOKEN_HASH:
        logger.warning(f"Admin registration failed: Invalid security token")
        return Response({
            'error': 'Invalid security token'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Create user data without the security token
    user_data = {k: v for k, v in request.data.items() if k != 'security_token'}
    
    # Add admin role
    try:
        admin_role = Role.objects.get(name='admin')
    except Role.DoesNotExist:
        logger.error("Admin role not found in database")
        return Response({
            'error': 'Admin role not found in database'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Use the standard serializer but bypass role validation
    serializer = UserSerializer(data=user_data)
    
    if serializer.is_valid():
        # Create user
        user = User.objects.create_user(
            username=user_data.get('username'),
            email=user_data.get('email'),
            password=user_data.get('password'),
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', ''),
            phone_number=user_data.get('phone_number', ''),
            address=user_data.get('address', ''),
            is_verified=True  # Auto-verify admin users
        )
        
        # Add the admin role
        user.roles.add(admin_role)
        user.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        logger.info(f"Admin user created successfully: {user.email}")
        
        return Response({
            'message': 'Admin user created successfully',
            'user': UserSerializer(user).data,
            'roles': [role.name for role in user.roles.all()],
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)
    
    logger.error(f"Admin registration failed: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)