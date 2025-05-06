from django.db import models
import uuid
from django.conf import settings

class HealthCareCategory(models.TextChoices):
    GENERAL = 'GENERAL', 'General Healthcare'
    PEDIATRIC = 'PEDIATRIC', 'Pediatric Healthcare'
    MENTAL = 'MENTAL', 'Mental Healthcare'
    DENTAL = 'DENTAL', 'Dental Healthcare'
    VISION = 'VISION', 'Vision Healthcare'
    OTHER = 'OTHER', 'Other'

class HealthCare(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(
        max_length=20,
        choices=HealthCareCategory.choices,
        default=HealthCareCategory.GENERAL
    )
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    website = models.URLField(blank=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    doctors = models.ManyToManyField('doctors.Doctor', related_name='healthcare_facilities', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.category}"

class PatientDoctorAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('users.Customer', on_delete=models.CASCADE, related_name='doctor_assignments')
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, related_name='patient_assignments')
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('patient', 'doctor')
        
    def __str__(self):
        return f"Patient: {self.patient.user.get_full_name()} - Doctor: {self.doctor.user.get_full_name()}"
