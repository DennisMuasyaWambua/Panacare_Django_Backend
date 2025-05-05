from rest_framework import serializers
from .models import User, Role, Customer

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
    
    def validate_role_names(self, value):
        """Validate that all role_names exist in the database"""
        if value:
            allowed_roles = ['doctor', 'patient']
            for role_name in value:
                if role_name not in allowed_roles:
                    raise serializers.ValidationError(f"Role '{role_name}' is not allowed. Choose from: {', '.join(allowed_roles)}")
                try:
                    Role.objects.get(name=role_name)
                except Role.DoesNotExist:
                    raise serializers.ValidationError(f"Role with name '{role_name}' does not exist")
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
                  'phone_number', 'address', 'roles', 'role_names', 'is_verified']
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
        # Extract role_names from validated_data, defaulting to empty list
        role_names = validated_data.pop('role_names', [])
        user = User.objects.create_user(**validated_data)
        
        # If no roles were specified, assign patient role by default
        if not role_names:
            try:
                default_role = Role.objects.get(name='patient')
                user.roles.add(default_role)
            except Role.DoesNotExist:
                # Log error if patient role doesn't exist
                import logging
                logger = logging.getLogger(__name__)
                logger.error("Default 'patient' role not found")
        else:
            # Assign all the specified roles - they've already been validated
            for role_name in role_names:
                role = Role.objects.get(name=role_name)  # This should never fail due to validation
                user.roles.add(role)
        
        return user

class CustomerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Customer
        fields = ['id', 'user', 'user_id', 'date_of_birth', 'gender', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
