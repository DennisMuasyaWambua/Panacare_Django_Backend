from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, Role, Patient

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description']

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        style={'input_type': 'password'}
    )
    roles = RoleSerializer(many=True, read_only=True)
    
    # Make role selection more user-friendly by using role names
    role_names = serializers.ListField(
        child=serializers.CharField(), 
        required=False,
        help_text="List of role names to assign to this user. Only doctor and patient roles are allowed."
    )
    
    # Allow a single role assignment
    role = serializers.CharField(
        required=True,
        write_only=True,
        help_text="Single role to assign to this user. Only doctor or patient role is allowed."
    )
    
    def validate_role_names(self, value):
        """Validate that all role_names exist in the database"""
        if value:
            # If it's an admin registration, allow 'admin' role
            if self.context.get('admin_registration'):
                allowed_roles = ['doctor', 'patient', 'admin']
            else:
                allowed_roles = ['doctor', 'patient']
                
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
                allowed_roles = ['doctor', 'patient', 'admin']
            else:
                allowed_roles = ['doctor', 'patient']
                
            if value not in allowed_roles:
                raise serializers.ValidationError(f"Role '{value}' is not allowed. Choose from: {', '.join(allowed_roles)}")
            try:
                Role.objects.get(name=value)
            except Role.DoesNotExist:
                raise serializers.ValidationError(f"Role with name '{value}' does not exist")
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
                  'phone_number', 'address', 'roles', 'role_names', 'role', 'is_verified']
        read_only_fields = ['id', 'is_verified']
        extra_kwargs = {
            'username': {'help_text': 'Your username'},
            'email': {'help_text': 'Your email address'},
            'first_name': {'help_text': 'Your first name'},
            'last_name': {'help_text': 'Your last name'},
            'phone_number': {'help_text': 'Your phone number'},
            'address': {'help_text': 'Your address'},
        }
    
    def create(self, validated_data):
        # Extract role_names and role from validated_data
        role_names = validated_data.pop('role_names', [])
        single_role = validated_data.pop('role', None)
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
