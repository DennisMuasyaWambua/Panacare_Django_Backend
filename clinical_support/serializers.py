from rest_framework import serializers
from .models import ClinicalDecisionRecord

class ClinicalDecisionInputSerializer(serializers.Serializer):
    """Serializer for clinical decision input data"""
    # Patient Information
    age = serializers.IntegerField(required=True)
    gender = serializers.ChoiceField(choices=['male', 'female', 'other'], required=True)
    weight = serializers.FloatField(required=True)
    height = serializers.FloatField(required=True)
    
    # Medical History
    high_blood_pressure = serializers.BooleanField(default=False)
    diabetes = serializers.BooleanField(default=False)
    on_medication = serializers.BooleanField(default=False)
    
    # Symptoms
    headache = serializers.BooleanField(default=False)
    dizziness = serializers.BooleanField(default=False)
    blurred_vision = serializers.BooleanField(default=False)
    palpitations = serializers.BooleanField(default=False)
    fatigue = serializers.BooleanField(default=False)
    chest_pain = serializers.BooleanField(default=False)
    frequent_thirst = serializers.BooleanField(default=False)
    loss_of_appetite = serializers.BooleanField(default=False)
    frequent_urination = serializers.BooleanField(default=False)
    other_symptoms = serializers.CharField(required=False, allow_blank=True)
    no_symptoms = serializers.BooleanField(default=False)
    
    # Vitals
    systolic_pressure = serializers.IntegerField(required=False, allow_null=True)
    diastolic_pressure = serializers.IntegerField(required=False, allow_null=True)
    blood_sugar = serializers.FloatField(required=False, allow_null=True)
    heart_rate = serializers.IntegerField(required=False, allow_null=True)
    
    # Lifestyle
    sleep_hours = serializers.FloatField(required=False, allow_null=True)
    exercise_minutes = serializers.IntegerField(required=False, allow_null=True)
    eats_unhealthy = serializers.BooleanField(default=False)
    smokes = serializers.BooleanField(default=False)
    consumes_alcohol = serializers.BooleanField(default=False)
    skips_medication = serializers.BooleanField(default=False)

class ClinicalDecisionRecordSerializer(serializers.ModelSerializer):
    """Serializer for the ClinicalDecisionRecord model"""
    class Meta:
        model = ClinicalDecisionRecord
        fields = '__all__'

class ClinicalDecisionResponseSerializer(serializers.Serializer):
    """Serializer for clinical decision support response"""
    analysis = serializers.CharField()
    recommendations = serializers.ListField(child=serializers.CharField())
    risk_level = serializers.CharField()
    record_id = serializers.UUIDField(required=False)
    blood_pressure_status = serializers.CharField(required=False)
    blood_sugar_status = serializers.CharField(required=False)