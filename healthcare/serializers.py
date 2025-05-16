from rest_framework import serializers
from .models import HealthCare, PatientDoctorAssignment
from doctors.serializers import DoctorSerializer
from doctors.models import Doctor
from users.models import Patient

class HealthCareSerializer(serializers.ModelSerializer):
    doctors = DoctorSerializer(many=True, read_only=True)
    doctor_ids = serializers.ListField(
        child=serializers.UUIDField(), 
        write_only=True, 
        required=False,
        help_text="List of doctor IDs to associate with this facility"
    )
    part_of_name = serializers.SerializerMethodField(read_only=True, help_text="Name of parent organization")
    
    # Add explicit field definitions with help_text for Swagger documentation
    name = serializers.CharField(help_text="Name of the healthcare facility")
    description = serializers.CharField(help_text="Description of the healthcare facility")
    category = serializers.ChoiceField(
        choices=HealthCare._meta.get_field('category').choices,
        help_text="Category of healthcare facility (GENERAL, PEDIATRIC, MENTAL, DENTAL, VISION, OTHER)"
    )
    address = serializers.CharField(help_text="Main address of the healthcare facility")
    phone_number = serializers.CharField(help_text="Contact phone number")
    email = serializers.EmailField(help_text="Contact email address")
    website = serializers.URLField(required=False, help_text="Website URL")
    is_verified = serializers.BooleanField(required=False, help_text="Whether the facility is verified")
    is_active = serializers.BooleanField(required=False, help_text="Whether the facility is active")
    identifier_system = serializers.CharField(required=False, help_text="FHIR identifier system URI")
    part_of = serializers.PrimaryKeyRelatedField(
        queryset=HealthCare.objects.all(), 
        required=False, 
        allow_null=True,
        help_text="ID of parent organization (if applicable)"
    )
    city = serializers.CharField(required=False, help_text="City")
    state = serializers.CharField(required=False, help_text="State/Province")
    postal_code = serializers.CharField(required=False, help_text="Postal/ZIP code")
    country = serializers.CharField(required=False, help_text="Country")
    
    class Meta:
        model = HealthCare
        fields = [
            'id', 'name', 'description', 'category', 'address', 
            'phone_number', 'email', 'website', 'is_verified', 
            'is_active', 'doctors', 'doctor_ids', 
            'identifier_system', 'part_of', 'part_of_name',
            'city', 'state', 'postal_code', 'country',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_part_of_name(self, obj):
        if obj.part_of:
            return obj.part_of.name
        return None
    
    def create(self, validated_data):
        doctor_ids = validated_data.pop('doctor_ids', [])
        healthcare = HealthCare.objects.create(**validated_data)
        
        from doctors.models import Doctor
        for doctor_id in doctor_ids:
            try:
                doctor = Doctor.objects.get(id=doctor_id)
                healthcare.doctors.add(doctor)
            except Doctor.DoesNotExist:
                pass
        
        return healthcare
    
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

class PatientDoctorAssignmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField(help_text="Patient's full name")
    doctor_name = serializers.SerializerMethodField(help_text="Doctor's full name")
    healthcare_facility_name = serializers.SerializerMethodField(read_only=True, help_text="Healthcare facility name")
    
    # Add explicit field definitions with help_text for Swagger documentation
    patient = serializers.PrimaryKeyRelatedField(
        queryset=Patient.objects.all(),
        help_text="ID of the patient"
    )
    doctor = serializers.PrimaryKeyRelatedField(
        queryset=Doctor.objects.all(),
        help_text="ID of the doctor"
    )
    notes = serializers.CharField(required=False, help_text="Assignment notes")
    is_active = serializers.BooleanField(required=False, help_text="Whether the assignment is active")
    status = serializers.ChoiceField(
        choices=PatientDoctorAssignment._meta.get_field('status').choices,
        required=False,
        help_text="FHIR Encounter status code"
    )
    encounter_type = serializers.ChoiceField(
        choices=PatientDoctorAssignment._meta.get_field('encounter_type').choices,
        required=False,
        help_text="FHIR Encounter type code"
    )
    identifier_system = serializers.CharField(required=False, help_text="FHIR identifier system URI")
    reason = serializers.CharField(required=False, help_text="Reason for the encounter")
    healthcare_facility = serializers.PrimaryKeyRelatedField(
        queryset=HealthCare.objects.all(),
        required=False,
        allow_null=True,
        help_text="ID of the healthcare facility where the encounter takes place"
    )
    scheduled_start = serializers.DateTimeField(required=False, allow_null=True, help_text="Scheduled start time")
    scheduled_end = serializers.DateTimeField(required=False, allow_null=True, help_text="Scheduled end time")
    actual_start = serializers.DateTimeField(required=False, allow_null=True, help_text="Actual start time")
    actual_end = serializers.DateTimeField(required=False, allow_null=True, help_text="Actual end time")
    
    class Meta:
        model = PatientDoctorAssignment
        fields = [
            'id', 'patient', 'doctor', 'patient_name', 'doctor_name', 
            'notes', 'is_active', 'status', 'encounter_type',
            'identifier_system', 'reason', 'healthcare_facility', 
            'healthcare_facility_name', 'scheduled_start', 'scheduled_end',
            'actual_start', 'actual_end', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    # No need for __init__ now that we import Patient at the top
    
    def get_patient_name(self, obj):
        return obj.patient.user.get_full_name() or obj.patient.user.username
    
    def get_doctor_name(self, obj):
        return obj.doctor.user.get_full_name() or obj.doctor.user.username
    
    def get_healthcare_facility_name(self, obj):
        if obj.healthcare_facility:
            return obj.healthcare_facility.name
        return None
    
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
