from rest_framework import serializers
from .models import Doctor, Education
from users.serializers import UserSerializer

class EducationSerializer(serializers.ModelSerializer):
    level_of_education = serializers.CharField(help_text="Education level (e.g., Bachelor's, Master's, PhD)")
    field = serializers.CharField(help_text="Field of study (e.g., Medicine, Computer Science)")
    institution = serializers.CharField(help_text="Educational institution name")
    start_date = serializers.DateField(required=False, allow_null=True, help_text="Start date of education")
    end_date = serializers.DateField(required=False, allow_null=True, help_text="End date of education")
    
    class Meta:
        model = Education
        fields = [
            'id', 'level_of_education', 'field', 'institution',
            'start_date', 'end_date'
        ]
        read_only_fields = ['id']
    
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

class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True, help_text="ID of user associated with this doctor")
    education_details = EducationSerializer(source='education', read_only=True)
    
    # Add explicit field definitions with help_text for Swagger documentation
    specialty = serializers.CharField(help_text="Medical specialty (e.g., Cardiology, Pediatrics)")
    license_number = serializers.CharField(help_text="Medical license number")
    experience_years = serializers.IntegerField(required=False, help_text="Years of professional experience")
    bio = serializers.CharField(required=False, help_text="Doctor's biography and professional information")
    education = serializers.PrimaryKeyRelatedField(queryset=Education.objects.all(), 
                                                help_text="ID of related education record")
    is_verified = serializers.BooleanField(required=False, help_text="Whether the doctor is verified")
    is_available = serializers.BooleanField(required=False, help_text="Whether the doctor is available for appointments")
    identifier_system = serializers.CharField(required=False, 
                                            help_text="FHIR identifier system URI")
    license_system = serializers.CharField(required=False, 
                                         help_text="FHIR license identifier system URI")
    communication_languages = serializers.CharField(required=False, 
                                                 help_text="Comma-separated list of language codes, e.g., 'en,es,fr'")
    
    class Meta:
        model = Doctor
        fields = [
            'id', 'user', 'user_id', 'specialty', 'license_number', 
            'experience_years', 'bio', 'education', 'education_details', 
            'is_verified', 'is_available', 'identifier_system', 
            'license_system', 'communication_languages',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
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
