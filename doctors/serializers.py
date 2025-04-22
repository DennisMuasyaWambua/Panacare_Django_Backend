from rest_framework import serializers
from .models import Doctor
from users.serializers import UserSerializer

class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Doctor
        fields = ['id', 'user', 'user_id', 'specialty', 'license_number', 'experience_years', 
                  'bio', 'education', 'is_verified', 'is_available', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
