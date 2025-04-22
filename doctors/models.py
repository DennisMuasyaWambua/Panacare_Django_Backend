from django.db import models
import uuid
from django.conf import settings

class Doctor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor')
    specialty = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50)
    experience_years = models.PositiveIntegerField(default=0)
    bio = models.TextField(blank=True)
    education = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.specialty}"
