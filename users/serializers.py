from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import User, Role, Patient, AuditLog, Location, CommunityHealthProvider, CHPPatientMessage, Clinician

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
        help_text="List of role names to assign to this user. Allowed roles: doctor, patient, clinician, and community_health_provider."
    )

    # Allow a single role assignment
    role = serializers.CharField(
        required=True,
        write_only=True,
        help_text="Single role to assign to this user. Allowed roles: doctor, patient, clinician, or community_health_provider."
    )
    
    def validate_role_names(self, value):
        """Validate that all role_names exist in the database"""
        if value:
            # If it's an admin registration, allow 'admin' role
            if self.context.get('admin_registration'):
                allowed_roles = ['doctor', 'patient', 'clinician', 'community_health_provider', 'admin']
            else:
                allowed_roles = ['doctor', 'patient', 'clinician', 'community_health_provider']

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
                allowed_roles = ['doctor', 'patient', 'clinician', 'community_health_provider', 'admin']
            else:
                allowed_roles = ['doctor', 'patient', 'clinician', 'community_health_provider']

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
    health_notes = serializers.CharField(required=False, help_text="Recent symptoms and health notes")

    class Meta:
        model = Patient
        fields = [
            'id', 'user', 'user_id', 'date_of_birth', 'gender',
            'active', 'marital_status', 'language', 'identifier_system',
            'blood_type', 'height_cm', 'weight_kg', 'allergies',
            'medical_conditions', 'medications', 'health_notes',
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


class ClinicianSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True, required=False)

    # Additional computed fields
    full_name = serializers.SerializerMethodField()
    contact_info = serializers.SerializerMethodField()
    verification_status = serializers.SerializerMethodField()
    verified_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Clinician
        fields = [
            'id', 'user', 'user_id', 'license_number', 'license_type',
            'issuing_authority', 'license_expiry_date', 'qualification',
            'years_of_experience', 'specialization', 'professional_bio',
            'skills', 'certifications', 'department', 'facility_name',
            'is_verified', 'is_active', 'verified_by', 'verification_date',
            'created_at', 'updated_at', 'full_name', 'contact_info',
            'verification_status', 'verified_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_verified', 'verified_by', 'verification_date']
        extra_kwargs = {
            'license_number': {'help_text': 'Professional license number'},
            'license_type': {'help_text': 'Type of license (e.g., RN, NP, PA, Clinical Officer)'},
            'issuing_authority': {'help_text': 'Licensing board or authority'},
            'license_expiry_date': {'help_text': 'License expiration date'},
            'qualification': {'help_text': 'Highest qualification (e.g., BSN, MSN, Diploma)'},
            'years_of_experience': {'help_text': 'Years of clinical experience'},
            'specialization': {'help_text': 'Clinical specialization (e.g., Emergency Care, Pediatrics)'},
            'professional_bio': {'help_text': 'Professional biography'},
            'skills': {'help_text': 'Key clinical skills and competencies'},
            'certifications': {'help_text': 'Additional certifications (comma-separated)'},
            'department': {'help_text': 'Department or unit'},
            'facility_name': {'help_text': 'Healthcare facility name'},
        }

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_contact_info(self, obj):
        return {
            'email': obj.user.email,
            'phone': obj.user.phone_number,
            'address': obj.user.address
        }

    def get_verification_status(self, obj):
        if obj.is_verified:
            return "verified"
        return "pending"

    def get_verified_by_name(self, obj):
        if obj.verified_by:
            return obj.verified_by.get_full_name() or obj.verified_by.username
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


class ClinicianVerificationSerializer(serializers.Serializer):
    """
    Serializer for admin to verify clinician credentials
    """
    clinician_id = serializers.UUIDField(required=True, help_text="Clinician ID to verify")
    is_verified = serializers.BooleanField(required=True, help_text="Verification status")
    verification_notes = serializers.CharField(required=False, allow_blank=True, help_text="Optional notes about verification")

    def validate_clinician_id(self, value):
        try:
            Clinician.objects.get(id=value)
        except Clinician.DoesNotExist:
            raise serializers.ValidationError("Clinician with the provided ID does not exist")
        return value


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
    health_notes = serializers.CharField(required=False)
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
    
    def validate_phone_number(self, value):
        """Validate and clean phone number to fit 15 character limit"""
        if value:
            # Remove common formatting characters
            cleaned_phone = ''.join(char for char in value if char.isdigit() or char == '+')
            # Ensure it fits the 15 character database constraint
            if len(cleaned_phone) > 15:
                raise serializers.ValidationError(
                    f"Phone number too long. Maximum 15 characters allowed. "
                    f"Current length: {len(cleaned_phone)}. "
                    f"Consider removing country code or formatting."
                )
            return cleaned_phone
        return value
    
    def validate_emergency_contact_phone(self, value):
        """Validate and clean emergency contact phone number"""
        if value:
            # Remove common formatting characters
            cleaned_phone = ''.join(char for char in value if char.isdigit() or char == '+')
            # Ensure it fits the 15 character database constraint
            if len(cleaned_phone) > 15:
                raise serializers.ValidationError(
                    f"Emergency contact phone number too long. Maximum 15 characters allowed. "
                    f"Current length: {len(cleaned_phone)}."
                )
            return cleaned_phone
        return value
    
    def validate_email(self, value):
        """Validate email uniqueness"""
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_username(self, value):
        """Validate username uniqueness if provided"""
        if value and User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value
    
    def create(self, validated_data):
        # Double-check email uniqueness to prevent race conditions
        email = validated_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        
        # Extract UUID fields
        patient_id = validated_data.pop('patient_id', None)
        user_id = validated_data.pop('user_id', None)
        
        # Extract patient-specific data
        patient_data = {}
        user_data = {}
        
        # Patient fields
        patient_fields = [
            'date_of_birth', 'gender', 'blood_type', 'height_cm', 'weight_kg',
            'allergies', 'medical_conditions', 'medications', 'health_notes',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship'
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
        
        # Generate username if not provided
        if not user_data.get('username'):
            # Generate username from first_name, last_name and a random suffix
            import secrets
            import string
            random_suffix = ''.join(secrets.choice(string.digits) for _ in range(4))
            base_username = f"{user_data.get('first_name', '').lower()}{user_data.get('last_name', '').lower()}{random_suffix}"
            # Ensure username is unique
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            user_data['username'] = username
        
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
            try:
                user.save()
            except Exception as e:
                # Handle potential duplicate key errors
                if 'duplicate key' in str(e).lower():
                    raise serializers.ValidationError(f"User with ID {user_id} already exists or username is taken")
                raise serializers.ValidationError(f"Error creating user: {str(e)}")
        else:
            # Auto-generate UUID
            try:
                user = User.objects.create_user(**user_data)
            except Exception as e:
                # Handle potential duplicate username errors
                if 'duplicate' in str(e).lower():
                    raise serializers.ValidationError("Username already exists. Please try again.")
                raise serializers.ValidationError(f"Error creating user: {str(e)}")
        
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
            try:
                patient.save()
            except Exception as e:
                # Clean up user if patient creation fails
                user.delete()
                if 'duplicate key' in str(e).lower():
                    raise serializers.ValidationError(f"Patient with ID {patient_id} already exists")
                raise serializers.ValidationError(f"Error creating patient: {str(e)}")
        else:
            # Auto-generate UUID using get_or_create to handle duplicates
            try:
                # Create defaults dict without the user field
                defaults = {k: v for k, v in patient_data.items() if k != 'user'}
                patient, created = Patient.objects.get_or_create(
                    user=user,
                    defaults=defaults
                )
                if not created:
                    # Patient already existed for this user, update it with new data
                    for key, value in defaults.items():
                        setattr(patient, key, value)
                    patient.save()
            except Exception as e:
                # Clean up user if patient creation fails
                user.delete()
                raise serializers.ValidationError(f"Error creating patient: {str(e)}")
        
        return {
            'user': user,
            'patient': patient,
            'temporary_password': password
        }


class CHPPatientMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    recipient_name = serializers.CharField(source='recipient.get_full_name', read_only=True)
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    chp_name = serializers.CharField(source='chp.user.get_full_name', read_only=True)
    
    class Meta:
        model = CHPPatientMessage
        fields = [
            'id', 'sender', 'recipient', 'patient', 'chp', 
            'message', 'is_read', 'created_at', 'updated_at',
            'sender_name', 'recipient_name', 'patient_name', 'chp_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class CHPAssignmentSerializer(serializers.Serializer):
    chp_id = serializers.UUIDField()
    patient_id = serializers.UUIDField()
    
    def validate(self, data):
        # Check if CHP exists
        try:
            CommunityHealthProvider.objects.get(id=data['chp_id'])
        except CommunityHealthProvider.DoesNotExist:
            raise serializers.ValidationError("CHP not found")
        
        # Check if Patient exists
        try:
            Patient.objects.get(id=data['patient_id'])
        except Patient.DoesNotExist:
            raise serializers.ValidationError("Patient not found")
        
        return data
