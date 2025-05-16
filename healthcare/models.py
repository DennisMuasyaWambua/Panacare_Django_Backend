from django.db import models
import uuid
from django.conf import settings

class HealthCareCategory(models.TextChoices):
    """
    Healthcare facility categories (maps to FHIR Organization.type)
    """
    GENERAL = 'GENERAL', 'General Healthcare'
    PEDIATRIC = 'PEDIATRIC', 'Pediatric Healthcare'
    MENTAL = 'MENTAL', 'Mental Healthcare'
    DENTAL = 'DENTAL', 'Dental Healthcare'
    VISION = 'VISION', 'Vision Healthcare'
    OTHER = 'OTHER', 'Other'
    
    @classmethod
    def to_fhir_code(cls, value):
        """Convert category to FHIR code"""
        code_map = {
            cls.GENERAL: "prov",
            cls.PEDIATRIC: "prov",
            cls.MENTAL: "prov",
            cls.DENTAL: "prov",
            cls.VISION: "prov",
            cls.OTHER: "other"
        }
        return code_map.get(value, "other")
    
    @classmethod
    def to_fhir_display(cls, value):
        """Convert category to FHIR display name"""
        display_map = {
            cls.GENERAL: "Healthcare Provider",
            cls.PEDIATRIC: "Pediatric Healthcare Provider",
            cls.MENTAL: "Mental Healthcare Provider",
            cls.DENTAL: "Dental Healthcare Provider",
            cls.VISION: "Vision Healthcare Provider",
            cls.OTHER: "Other Healthcare Provider"
        }
        return display_map.get(value, "Other")

class HealthCare(models.Model):
    """
    HealthCare model (maps to FHIR Organization resource)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(
        max_length=20,
        choices=HealthCareCategory.choices,
        default=HealthCareCategory.GENERAL
    )
    
    # Contact information
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    website = models.URLField(blank=True)
    
    # FHIR status fields
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Relationships
    doctors = models.ManyToManyField('doctors.Doctor', related_name='healthcare_facilities', blank=True)
    
    # Additional FHIR-compliant fields
    identifier_system = models.CharField(max_length=255, default="urn:panacare:organization", blank=True)
    part_of = models.ForeignKey('self', null=True, blank=True, related_name='sub_organizations', on_delete=models.SET_NULL)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True, default="United States")
    
    # Metadata fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.category}"
    
    def to_fhir_json(self):
        """Return FHIR-compliant representation of healthcare facility"""
        # Get FHIR code and display for category
        category_code = HealthCareCategory.to_fhir_code(self.category)
        category_display = HealthCareCategory.to_fhir_display(self.category)
        
        fhir_json = {
            "resourceType": "Organization",
            "id": str(self.id),
            "identifier": [
                {
                    "system": self.identifier_system,
                    "value": str(self.id)
                }
            ],
            "active": self.is_active and self.is_verified,
            "type": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/organization-type",
                            "code": category_code,
                            "display": category_display
                        }
                    ],
                    "text": self.get_category_display()
                }
            ],
            "name": self.name,
            "telecom": [
                {
                    "system": "phone",
                    "value": self.phone_number,
                    "use": "work"
                } if self.phone_number else None,
                {
                    "system": "email",
                    "value": self.email,
                    "use": "work"
                } if self.email else None,
                {
                    "system": "url",
                    "value": self.website,
                    "use": "work"
                } if self.website else None
            ],
            "address": [
                {
                    "use": "work",
                    "line": [self.address] if self.address else [],
                    "city": self.city,
                    "state": self.state,
                    "postalCode": self.postal_code,
                    "country": self.country,
                    "text": self.address
                }
            ]
        }
        
        # Add part_of if applicable
        if self.part_of:
            fhir_json["partOf"] = {
                "reference": f"Organization/{self.part_of.id}",
                "display": self.part_of.name
            }
        
        return fhir_json

class EncounterStatus(models.TextChoices):
    """
    FHIR Encounter status codes
    """
    PLANNED = 'planned', 'Planned'
    ARRIVED = 'arrived', 'Arrived'
    TRIAGED = 'triaged', 'Triaged'
    IN_PROGRESS = 'in-progress', 'In Progress'
    ONLEAVE = 'onleave', 'On Leave'
    FINISHED = 'finished', 'Finished'
    CANCELLED = 'cancelled', 'Cancelled'
    ENTERED_IN_ERROR = 'entered-in-error', 'Entered in Error'
    UNKNOWN = 'unknown', 'Unknown'

class EncounterType(models.TextChoices):
    """
    FHIR Encounter type codes
    """
    AMBULATORY = 'AMB', 'Ambulatory'
    EMERGENCY = 'EMER', 'Emergency'
    FIELD = 'FLD', 'Field'
    HOME_HEALTH = 'HH', 'Home Health'
    INPATIENT_ACUTE = 'IMP', 'Inpatient Acute'
    VIRTUAL = 'VR', 'Virtual'
    OBSERVATION = 'OBS', 'Observation'
    OUTPATIENT = 'OP', 'Outpatient'
    STANDARD = 'SS', 'Standard Scheduled'

class PatientDoctorAssignment(models.Model):
    """
    PatientDoctorAssignment model (maps to FHIR Encounter resource)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('users.Patient', on_delete=models.CASCADE, related_name='doctor_assignments')
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, related_name='patient_assignments')
    
    # FHIR Encounter fields
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    status = models.CharField(
        max_length=20,
        choices=EncounterStatus.choices,
        default=EncounterStatus.PLANNED
    )
    encounter_type = models.CharField(
        max_length=10,
        choices=EncounterType.choices,
        default=EncounterType.STANDARD
    )
    
    # Additional FHIR-compliant fields
    identifier_system = models.CharField(max_length=255, default="urn:panacare:encounter", blank=True)
    reason = models.CharField(max_length=255, blank=True)
    healthcare_facility = models.ForeignKey(HealthCare, on_delete=models.SET_NULL, null=True, blank=True, related_name='encounters')
    scheduled_start = models.DateTimeField(null=True, blank=True)
    scheduled_end = models.DateTimeField(null=True, blank=True)
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    
    # Metadata fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('patient', 'doctor')
        
    def __str__(self):
        return f"Patient: {self.patient.user.get_full_name()} - Doctor: {self.doctor.user.get_full_name()}"
    
    def to_fhir_json(self):
        """Return FHIR-compliant representation of patient-doctor assignment"""
        # Set status based on is_active flag if not explicitly set
        status = self.status
        if not status:
            status = EncounterStatus.IN_PROGRESS if self.is_active else EncounterStatus.FINISHED
            
        # Determine period based on available dates
        period = {}
        if self.actual_start:
            period["start"] = self.actual_start.isoformat()
        elif self.scheduled_start:
            period["start"] = self.scheduled_start.isoformat()
        else:
            period["start"] = self.created_at.isoformat()
            
        if self.actual_end:
            period["end"] = self.actual_end.isoformat()
        elif not self.is_active:
            period["end"] = self.updated_at.isoformat()
            
        # Create main FHIR JSON
        fhir_json = {
            "resourceType": "Encounter",
            "id": str(self.id),
            "identifier": [
                {
                    "system": self.identifier_system,
                    "value": str(self.id)
                }
            ],
            "status": status,
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": self.encounter_type,
                "display": self.get_encounter_type_display()
            },
            "subject": {
                "reference": f"Patient/{self.patient.id}",
                "display": self.patient.user.get_full_name() or self.patient.user.username
            },
            "participant": [
                {
                    "individual": {
                        "reference": f"Practitioner/{self.doctor.id}",
                        "display": self.doctor.user.get_full_name() or self.doctor.user.username
                    },
                    "type": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                                    "code": "PPRF",
                                    "display": "Primary performer"
                                }
                            ]
                        }
                    ]
                }
            ],
            "period": period
        }
        
        # Add reason if available
        if self.reason or self.notes:
            fhir_json["reasonCode"] = [
                {
                    "text": self.reason or self.notes
                }
            ]
        
        # Add healthcare service location if available
        if self.healthcare_facility:
            fhir_json["serviceProvider"] = {
                "reference": f"Organization/{self.healthcare_facility.id}",
                "display": self.healthcare_facility.name
            }
            
        return fhir_json
