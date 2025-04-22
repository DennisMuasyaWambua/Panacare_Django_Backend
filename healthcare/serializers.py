from rest_framework import serializers
from .models import HealthCare
from doctors.serializers import DoctorSerializer

class HealthCareSerializer(serializers.ModelSerializer):
    doctors = DoctorSerializer(many=True, read_only=True)
    doctor_ids = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    
    class Meta:
        model = HealthCare
        fields = ['id', 'name', 'description', 'category', 'address', 'phone_number', 
                  'email', 'website', 'is_verified', 'is_active', 'doctors', 'doctor_ids', 
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
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
