from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, Role, Patient, AuditLog, Location, CommunityHealthProvider, EmailVerification

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description']


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'level', 'parent']
        read_only_fields = ['id']

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        style={'input_type': 'password'}
    )
    roles = RoleSerializer(many=True, read_only=True)
    location = LocationSerializer(read_only=True)
    location_id = serializers.UUIDField(required=False, write_only=True, help_text="UUID of the user's location")
    
    # Make role selection more user-friendly by using role names
    role_names = serializers.ListField(
        child=serializers.CharField(), 
        required=False,
        help_text="List of role names to assign to this user. Only doctor, patient, and community_health_provider roles are allowed."
    )
    
    # Allow a single role assignment
    role = serializers.CharField(
        required=True,
        write_only=True,
        help_text="Single role to assign to this user. Only doctor, patient, or community_health_provider role is allowed."
    )
    
    def validate_role_names(self, value):
        """Validate that all role_names exist in the database"""
        if value:
            # If it's an admin registration, allow 'admin' role
            if self.context.get('admin_registration'):
                allowed_roles = ['doctor', 'patient', 'community_health_provider', 'admin']
            else:
                allowed_roles = ['doctor', 'patient', 'community_health_provider']
                
            for role_name in value:
                if role_name not in allowed_roles:
                    raise serializers.ValidationError(f"Role '{role_name}' is not allowed. Choose from: {', '.join(allowed_roles)}")
                try:
                    Role.objects.get(name=role_name)
                except Role.DoesNotExist:
                    raise serializers.ValidationError(f"Role with name '{role_name}' does not exist")
        return value
        
    def validate_role(self, value):
        """Validate that the role exists in the database"""
        if value:
            # If it's an admin registration, allow 'admin' role
            if self.context.get('admin_registration'):
                allowed_roles = ['doctor', 'patient', 'community_health_provider', 'admin']
            else:
                allowed_roles = ['doctor', 'patient', 'community_health_provider']
                
            if value not in allowed_roles:
                raise serializers.ValidationError(f"Role '{value}' is not allowed. Choose from: {', '.join(allowed_roles)}")
            try:
                Role.objects.get(name=value)
            except Role.DoesNotExist:
                raise serializers.ValidationError(f"Role with name '{value}' does not exist")
        return value
    
    def validate_location_id(self, value):
        """Validate that the location exists in the database"""
        if value:
            try:
                Location.objects.get(id=value)
            except Location.DoesNotExist:
                raise serializers.ValidationError("Location with the provided ID does not exist")
        return value
    
    def to_representation(self, instance):
        """Add available roles to the representation"""
        ret = super().to_representation(instance)
        # Add available roles when appropriate
        if self.context.get('request') and self.context['request'].method in ['GET', 'POST']:
            available_roles = Role.objects.exclude(name='admin')
            ret['available_roles'] = RoleSerializer(available_roles, many=True).data
        return ret
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 
                  'phone_number', 'address', 'location', 'location_id', 'roles', 'role_names', 'role', 'is_verified']
        read_only_fields = ['id', 'is_verified']
        extra_kwargs = {
            'username': {'help_text': 'Your username'},
            'email': {'help_text': 'Your email address'},
            'first_name': {'help_text': 'Your first name'},
            'last_name': {'help_text': 'Your last name'},
            'phone_number': {'help_text': 'Your phone number'},
            'address': {'help_text': 'Your address'},
            'location_id': {'help_text': 'UUID of your location (village level preferred)'},
        }
    
    def create(self, validated_data):
        # Extract role_names and role from validated_data
        role_names = validated_data.pop('role_names', [])
        single_role = validated_data.pop('role', None)
        location_id = validated_data.pop('location_id', None)
        
        # Handle location assignment
        if location_id:
            try:
                location = Location.objects.get(id=location_id)
                validated_data['location'] = location
            except Location.DoesNotExist:
                pass  # This should not happen due to validation
        
        user = User.objects.create_user(**validated_data)
        
        # Check if a single role was specified
        if single_role:
            try:
                role = Role.objects.get(name=single_role)
                user.roles.add(role)
            except Role.DoesNotExist:
                # This should never happen due to validation
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Role '{single_role}' not found")
        # Otherwise, check role_names
        elif role_names:
            # Assign all the specified roles - they've already been validated
            for role_name in role_names:
                role = Role.objects.get(name=role_name)
                user.roles.add(role)
        # No default role assignment anymore - user must provide a role
        
        return user

class PatientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True)
    
    # Add explicit field definitions with help_text for Swagger documentation
    date_of_birth = serializers.DateField(required=False, allow_null=True, 
                                        help_text="Patient's date of birth")
    gender = serializers.ChoiceField(choices=['male', 'female', 'other', 'unknown'], required=False,
                                   help_text="Patient's gender")
    active = serializers.BooleanField(required=False, help_text="Whether the patient record is active")
    marital_status = serializers.ChoiceField(choices=['M', 'S', 'D', 'W', 'U'], required=False,
                                           help_text="Marital status (M=Married, S=Single, D=Divorced, W=Widowed, U=Unknown)")
    language = serializers.CharField(required=False, help_text="Preferred language code, e.g. 'en'")
    blood_type = serializers.ChoiceField(choices=['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', ''], 
                                       required=False, help_text="Blood type")
    height_cm = serializers.IntegerField(required=False, allow_null=True, help_text="Height in centimeters")
    weight_kg = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True,
                                       help_text="Weight in kilograms")
    allergies = serializers.CharField(required=False, help_text="Known allergies")
    medical_conditions = serializers.CharField(required=False, help_text="Pre-existing medical conditions")
    medications = serializers.CharField(required=False, help_text="Current medications")
    
    class Meta:
        model = Patient
        fields = [
            'id', 'user', 'user_id', 'date_of_birth', 'gender', 
            'active', 'marital_status', 'language', 'identifier_system',
            'blood_type', 'height_cm', 'weight_kg', 'allergies', 
            'medical_conditions', 'medications', 
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
            'insurance_provider', 'insurance_policy_number', 'insurance_group_number',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'emergency_contact_name': {'help_text': 'Emergency contact name'},
            'emergency_contact_phone': {'help_text': 'Emergency contact phone number'},
            'emergency_contact_relationship': {'help_text': 'Relationship to emergency contact'},
            'insurance_provider': {'help_text': 'Insurance provider name'},
            'insurance_policy_number': {'help_text': 'Insurance policy number'},
            'insurance_group_number': {'help_text': 'Insurance group number'},
            'identifier_system': {'help_text': 'FHIR identifier system URI'}
        }
    
    def to_representation(self, instance):
        """
        If FHIR format is requested, return FHIR JSON representation.
        """
        request = self.context.get('request')
        
        # Default to standard representation
        if not request or not request.query_params.get('format') == 'fhir':
            return super().to_representation(instance)
        
        # Return FHIR format
        return instance.to_fhir_json()


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True, help_text="User's current password")
    new_password = serializers.CharField(required=True, help_text="New password to set")
    
    def validate_new_password(self, value):
        """
        Validate the new password using Django's validators.
        """
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value


class EmailChangeSerializer(serializers.Serializer):
    password = serializers.CharField(required=True, help_text="User's current password for verification")
    new_email = serializers.EmailField(required=True, help_text="New email address")
    
    def validate_new_email(self, value):
        """
        Validate that the email address isn't already in use.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email address is already in use.")
        return value


class PhoneChangeSerializer(serializers.Serializer):
    password = serializers.CharField(required=True, help_text="User's current password for verification")
    new_phone_number = serializers.CharField(required=True, help_text="New phone number")


class ContactUsSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, help_text="Your name")
    email = serializers.EmailField(required=True, help_text="Your email address")
    subject = serializers.CharField(required=True, help_text="Message subject")
    message = serializers.CharField(required=True, help_text="Your message")


class SupportRequestSerializer(serializers.Serializer):
    subject = serializers.CharField(required=True, help_text="Support request subject")
    message = serializers.CharField(required=True, help_text="Detailed support request")
    request_type = serializers.ChoiceField(
        required=True,
        choices=[
            ('technical', 'Technical Issue'),
            ('billing', 'Billing Question'),
            ('account', 'Account Issue'),
            ('feedback', 'Feedback'),
            ('other', 'Other')
        ],
        help_text="Type of support request"
    )
    priority = serializers.ChoiceField(
        required=False,
        default='medium',
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('urgent', 'Urgent')
        ],
        help_text="Priority level of the request"
    )


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, help_text="Email address associated with your account")


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for AuditLog model with read-only fields for security
    """
    activity_display = serializers.CharField(source='get_activity_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    formatted_time_spent = serializers.ReadOnlyField()
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'username', 'activity', 'activity_display', 'email_address', 
            'role', 'time_spent', 'formatted_time_spent', 'date_joined', 
            'last_active', 'status', 'status_display', 'ip_address', 
            'user_agent', 'session_id', 'details', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'username', 'activity', 'activity_display', 'email_address',
            'role', 'time_spent', 'formatted_time_spent', 'date_joined',
            'last_active', 'status', 'status_display', 'ip_address',
            'user_agent', 'session_id', 'details', 'created_at', 'updated_at'
        ]
        
    def to_representation(self, instance):
        """
        Customize the representation to include additional computed fields
        """
        ret = super().to_representation(instance)
        
        # Add user full name if available
        if hasattr(instance.user, 'first_name') and hasattr(instance.user, 'last_name'):
            ret['full_name'] = f"{instance.user.first_name} {instance.user.last_name}".strip()
            if not ret['full_name']:
                ret['full_name'] = instance.username
        else:
            ret['full_name'] = instance.username
            
        # Format dates for better readability
        if instance.created_at:
            ret['formatted_created_at'] = instance.created_at.strftime('%d %B %Y')
        if instance.last_active:
            ret['formatted_last_active'] = instance.last_active.strftime('%d %B %Y')
        if instance.date_joined:
            ret['formatted_date_joined'] = instance.date_joined.strftime('%d %B %Y')
            
        return ret


class AuditLogFilterSerializer(serializers.Serializer):
    """
    Serializer for audit log filtering parameters
    """
    search = serializers.CharField(required=False, help_text="Search by username or email")
    role = serializers.CharField(required=False, help_text="Filter by user role")
    status = serializers.ChoiceField(
        choices=AuditLog.STATUS_CHOICES,
        required=False,
        help_text="Filter by status"
    )
    activity = serializers.ChoiceField(
        choices=AuditLog.ACTIVITY_CHOICES,
        required=False,
        help_text="Filter by activity type"
    )
    date_from = serializers.DateField(required=False, help_text="Filter from date (YYYY-MM-DD)")
    date_to = serializers.DateField(required=False, help_text="Filter to date (YYYY-MM-DD)")
    ordering = serializers.ChoiceField(
        choices=[
            ('-created_at', 'Newest first'),
            ('created_at', 'Oldest first'),
            ('-last_active', 'Most recently active first'),
            ('last_active', 'Least recently active first'),
            ('username', 'Username A-Z'),
            ('-username', 'Username Z-A'),
        ],
        default='-created_at',
        required=False,
        help_text="Order results"
    )


class CommunityHealthProviderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True, required=False)
    
    # Additional computed fields
    full_name = serializers.SerializerMethodField()
    contact_info = serializers.SerializerMethodField()
    location_info = serializers.SerializerMethodField()
    
    class Meta:
        model = CommunityHealthProvider
        fields = [
            'id', 'user', 'user_id', 'certification_number', 'years_of_experience', 
            'specialization', 'service_area', 'languages_spoken', 'is_active', 
            'availability_hours', 'created_at', 'updated_at', 'full_name', 
            'contact_info', 'location_info'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    
    def get_contact_info(self, obj):
        return {
            'email': obj.user.email,
            'phone': obj.user.phone_number,
            'address': obj.user.address
        }
    
    def get_location_info(self, obj):
        if obj.user.location:
            return {
                'id': str(obj.user.location.id),
                'name': obj.user.location.name,
                'level': obj.user.location.level
            }
        return None
    
    def create(self, validated_data):
        user_id = validated_data.pop('user_id', None)
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                validated_data['user'] = user
            except User.DoesNotExist:
                raise serializers.ValidationError("User with the provided ID does not exist")
        
        return super().create(validated_data)


class CHPPatientCreateSerializer(serializers.Serializer):
    """
    Serializer for Community Health Provider to create patients
    Supports pre-generated UUIDs for offline functionality
    """
    # Pre-generated UUID fields (optional for offline mode)
    patient_id = serializers.UUIDField(required=False, help_text="Pre-generated patient UUID for offline mode")
    user_id = serializers.UUIDField(required=False, help_text="Pre-generated user UUID for offline mode")
    
    # User fields
    username = serializers.CharField(required=False)
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone_number = serializers.CharField(required=False)
    address = serializers.CharField(required=False)
    location_id = serializers.UUIDField(required=False)
    
    # Patient-specific fields
    date_of_birth = serializers.DateField(required=False)
    gender = serializers.ChoiceField(
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other'), ('unknown', 'Unknown')],
        required=False
    )
    blood_type = serializers.ChoiceField(
        choices=[('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), 
                ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'), ('', 'Unknown')],
        required=False
    )
    height_cm = serializers.IntegerField(required=False)
    weight_kg = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    allergies = serializers.CharField(required=False)
    medical_conditions = serializers.CharField(required=False)
    medications = serializers.CharField(required=False)
    emergency_contact_name = serializers.CharField(required=False)
    emergency_contact_phone = serializers.CharField(required=False)
    emergency_contact_relationship = serializers.CharField(required=False)
    
    def validate_location_id(self, value):
        if value:
            try:
                Location.objects.get(id=value)
            except Location.DoesNotExist:
                raise serializers.ValidationError("Location with the provided ID does not exist")
        return value
    
    def validate_user_id(self, value):
        if value:
            if User.objects.filter(id=value).exists():
                raise serializers.ValidationError("User with this ID already exists")
        return value
    
    def validate_patient_id(self, value):
        if value:
            if Patient.objects.filter(id=value).exists():
                raise serializers.ValidationError("Patient with this ID already exists")
        return value
    
    def create(self, validated_data):
        # Extract UUID fields
        patient_id = validated_data.pop('patient_id', None)
        user_id = validated_data.pop('user_id', None)
        
        # Extract patient-specific data
        patient_data = {}
        user_data = {}
        
        # Patient fields
        patient_fields = [
            'date_of_birth', 'gender', 'blood_type', 'height_cm', 'weight_kg',
            'allergies', 'medical_conditions', 'medications', 'emergency_contact_name',
            'emergency_contact_phone', 'emergency_contact_relationship'
        ]
        
        for field in patient_fields:
            if field in validated_data:
                patient_data[field] = validated_data.pop(field)
        
        # Handle location
        location_id = validated_data.pop('location_id', None)
        if location_id:
            user_data['location'] = Location.objects.get(id=location_id)
        
        # Prepare user data
        user_data.update(validated_data)
        
        # Generate password for patient
        import secrets
        import string
        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
        user_data['password'] = password
        
        # Create user with optional pre-generated UUID
        if user_id:
            # Use pre-generated UUID - need to create manually
            user_data['id'] = user_id
            user = User(**user_data)
            user.set_password(user_data['password'])
            user.save()
        else:
            # Auto-generate UUID
            user = User.objects.create_user(**user_data)
        
        # Add patient role
        try:
            patient_role = Role.objects.get(name='patient')
            user.roles.add(patient_role)
        except Role.DoesNotExist:
            pass
        
        # Create patient profile with optional pre-generated UUID
        patient_data['user'] = user
        
        # Set the CHP who created this patient
        chp = self.context.get('chp')
        if chp:
            patient_data['created_by_chp'] = chp
        
        if patient_id:
            # Use pre-generated UUID
            patient_data['id'] = patient_id
            patient = Patient(**patient_data)
            patient.save()
        else:
            # Auto-generate UUID
            patient = Patient.objects.create(**patient_data)
        
        return {
            'user': user,
            'patient': patient,
            'temporary_password': password
        }

class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification with 6-digit code"""
    email = serializers.EmailField()
    verification_code = serializers.CharField(max_length=6, min_length=6)
    
    def validate(self, data):
        email = data['email']
        code = data['verification_code']
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email address.")
        
        try:
            verification = EmailVerification.objects.get(
                user=user,
                verification_code=code,
                is_used=False
            )
        except EmailVerification.DoesNotExist:
            raise serializers.ValidationError("Invalid verification code.")
        
        if verification.is_expired():
            raise serializers.ValidationError("Verification code has expired.")
        
        data['user'] = user
        data['verification'] = verification
        return data

class ResendVerificationSerializer(serializers.Serializer):
    """Serializer for resending verification email"""
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            if user.is_verified:
                raise serializers.ValidationError("Email is already verified.")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
