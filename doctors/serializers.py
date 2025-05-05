from rest_framework import serializers
from .models import Doctor, Education
from users.serializers import UserSerializer

class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = ['id', 'level_of_education', 'field', 'institution']
        read_only_fields = ['id']

class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True)
    education_details = EducationSerializer(source='education', read_only=True)
    
    class Meta:
        model = Doctor
        fields = ['id', 'user', 'user_id', 'specialty', 'license_number', 'experience_years', 
                  'bio', 'education', 'education_details', 'is_verified', 'is_available', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
