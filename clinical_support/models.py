from django.db import models
import uuid
from users.models import Patient

class ClinicalDecisionRecord(models.Model):
    """Model for storing clinical decision support records"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True, related_name='clinical_decisions')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Patient Information
    age = models.IntegerField()
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    weight = models.FloatField(help_text="Weight in kilograms")
    height = models.FloatField(help_text="Height in centimeters")
    
    # Medical History
    high_blood_pressure = models.BooleanField(default=False, help_text="Has the patient been diagnosed with high blood pressure?")
    diabetes = models.BooleanField(default=False, help_text="Has the patient been diagnosed with diabetes?")
    on_medication = models.BooleanField(default=False, help_text="Is the patient currently on medication?")
    
    # Symptoms
    headache = models.BooleanField(default=False)
    dizziness = models.BooleanField(default=False)
    blurred_vision = models.BooleanField(default=False)
    palpitations = models.BooleanField(default=False)
    fatigue = models.BooleanField(default=False)
    chest_pain = models.BooleanField(default=False)
    frequent_thirst = models.BooleanField(default=False)
    loss_of_appetite = models.BooleanField(default=False)
    frequent_urination = models.BooleanField(default=False)
    other_symptoms = models.TextField(blank=True, null=True)
    no_symptoms = models.BooleanField(default=False, help_text="None of the above symptoms")
    
    # Vitals
    systolic_pressure = models.IntegerField(null=True, blank=True, help_text="Systolic blood pressure")
    diastolic_pressure = models.IntegerField(null=True, blank=True, help_text="Diastolic blood pressure")
    blood_sugar = models.FloatField(null=True, blank=True, help_text="Blood sugar in mg/dL")
    heart_rate = models.IntegerField(null=True, blank=True, help_text="Heart rate in BPM")
    
    # Lifestyle
    sleep_hours = models.FloatField(null=True, blank=True, help_text="Hours of sleep per day")
    exercise_minutes = models.IntegerField(null=True, blank=True, help_text="Minutes of exercise per day")
    eats_unhealthy = models.BooleanField(default=False, help_text="Regularly eats salty or sugary foods")
    smokes = models.BooleanField(default=False, help_text="Patient smokes")
    consumes_alcohol = models.BooleanField(default=False, help_text="Patient consumes alcohol")
    skips_medication = models.BooleanField(default=False, help_text="Patient sometimes skips medication")
    
    # Analysis and Recommendations
    analysis = models.TextField(blank=True, null=True, help_text="Analysis of patient data")
    recommendations = models.TextField(blank=True, null=True, help_text="Recommendations based on analysis")
    risk_level = models.CharField(max_length=20, blank=True, null=True, help_text="Assessed risk level")
    
    def __str__(self):
        return f"Clinical Decision Record {self.id}"
