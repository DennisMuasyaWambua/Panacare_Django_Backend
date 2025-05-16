from django.db import models
import uuid
from django.conf import settings


class Education(models.Model):
    """
    Education model (maps to FHIR Practitioner.qualification)
    """
    level_of_education = models.CharField(max_length=100)
    field = models.CharField(max_length=100)
    institution = models.CharField(max_length=100)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.level_of_education} in {self.field} from {self.institution}"
    
    def to_fhir_json(self):
        """Return FHIR-compliant representation of education"""
        return {
            "code": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0360",
                        "code": self.level_of_education.upper().replace(" ", "_"),
                        "display": self.level_of_education
                    }
                ],
                "text": f"{self.level_of_education} in {self.field}"
            },
            "issuer": {
                "display": self.institution
            },
            "period": {
                "start": self.start_date.isoformat() if self.start_date else None,
                "end": self.end_date.isoformat() if self.end_date else None
            }
        }

class Doctor(models.Model):
    """
    Doctor model (maps to FHIR Practitioner resource)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor')
    
    # FHIR Practitioner fields
    specialty = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50)
    experience_years = models.PositiveIntegerField(default=0)
    bio = models.TextField(blank=True)
    education = models.ForeignKey(Education, on_delete=models.CASCADE, related_name="doctor_education", null=False)
    
    # FHIR status fields
    is_verified = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    
    # Additional FHIR-compliant fields
    identifier_system = models.CharField(max_length=255, default="urn:panacare:practitioner", blank=True)
    license_system = models.CharField(max_length=255, default="urn:panacare:license", blank=True)
    communication_languages = models.CharField(max_length=255, blank=True, default="en")
    
    # Metadata fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.specialty}"
    
    def to_fhir_json(self):
        """Return FHIR-compliant representation of doctor"""
        # Clean languages
        languages = [lang.strip() for lang in self.communication_languages.split(',') if lang.strip()]
        if not languages:
            languages = ['en']
            
        return {
            "resourceType": "Practitioner",
            "id": str(self.id),
            "identifier": [
                {
                    "system": self.identifier_system,
                    "value": str(self.id)
                },
                {
                    "system": self.license_system,
                    "value": self.license_number,
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "MD",
                                "display": "Medical License number"
                            }
                        ]
                    }
                }
            ],
            "active": self.is_available and self.is_verified and self.user.is_active,
            "name": [
                {
                    "use": "official",
                    "family": self.user.last_name,
                    "given": [self.user.first_name],
                    "prefix": ["Dr."]
                }
            ],
            "telecom": [
                {
                    "system": "email",
                    "value": self.user.email,
                    "use": "work"
                },
                {
                    "system": "phone",
                    "value": self.user.phone_number,
                    "use": "work"
                } if self.user.phone_number else None
            ],
            "address": [
                {
                    "use": "work",
                    "text": self.user.address
                }
            ] if self.user.address else [],
            "qualification": [
                self.education.to_fhir_json(),
                {
                    "code": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0360",
                                "code": self.specialty.upper().replace(" ", "_"),
                                "display": self.specialty
                            }
                        ],
                        "text": self.specialty
                    }
                }
            ],
            "communication": [
                {
                    "coding": [
                        {
                            "system": "urn:ietf:bcp:47",
                            "code": lang
                        }
                    ]
                } for lang in languages
            ]
        }

