from rest_framework import serializers
from .models import User, Role, Customer

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description']

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    roles = RoleSerializer(many=True, read_only=True)
    role_ids = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 
                  'phone_number', 'address', 'roles', 'role_ids', 'is_verified']
        read_only_fields = ['id', 'is_verified']
    
    def create(self, validated_data):
        role_ids = validated_data.pop('role_ids', [])
        user = User.objects.create_user(**validated_data)
        
        for role_id in role_ids:
            try:
                role = Role.objects.get(id=role_id)
                user.roles.add(role)
            except Role.DoesNotExist:
                pass
        
        return user

class CustomerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Customer
        fields = ['id', 'user', 'user_id', 'date_of_birth', 'gender', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
