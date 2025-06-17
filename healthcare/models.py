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


class DoctorAvailability(models.Model):
    """
    Doctor's scheduled availability times
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, related_name='availabilities')
    
    # Schedule details
    day_of_week = models.IntegerField(choices=[
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ])
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_recurring = models.BooleanField(default=True)
    
    # Optional specific date (for non-recurring availability)
    specific_date = models.DateField(null=True, blank=True)
    
    # Status
    is_available = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Doctor Availability"
        verbose_name_plural = "Doctor Availabilities"
        
    def __str__(self):
        day_name = dict(self._meta.get_field('day_of_week').choices).get(self.day_of_week)
        if self.specific_date:
            return f"Dr. {self.doctor.user.get_full_name()} available on {self.specific_date.strftime('%Y-%m-%d')} from {self.start_time} to {self.end_time}"
        return f"Dr. {self.doctor.user.get_full_name()} available on {day_name}s from {self.start_time} to {self.end_time}"


class AppointmentStatus(models.TextChoices):
    """
    FHIR Appointment status codes
    """
    PROPOSED = 'proposed', 'Proposed'
    PENDING = 'pending', 'Pending'
    BOOKED = 'booked', 'Booked'
    ARRIVED = 'arrived', 'Arrived'
    FULFILLED = 'fulfilled', 'Fulfilled'
    CANCELLED = 'cancelled', 'Cancelled'
    NOSHOW = 'noshow', 'No Show'
    SCHEDULED = 'scheduled', 'Scheduled'
    ENTERED_IN_ERROR = 'entered-in-error', 'Entered in Error'


class Appointment(models.Model):
    """
    Appointment model (maps to FHIR Appointment resource)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('users.Patient', on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, related_name='appointments')
    
    # Appointment details
    appointment_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.BOOKED
    )
    
    # Appointment type and reason
    appointment_type = models.CharField(max_length=50, choices=[
        ('routine', 'Routine Checkup'),
        ('follow-up', 'Follow Up'),
        ('emergency', 'Emergency'),
        ('consultation', 'Consultation'),
        ('procedure', 'Procedure'),
        ('checkup', 'Checkup'),
        ('other', 'Other')
    ], default='consultation')
    reason = models.TextField(blank=True)
    
    # Consultation details filled by doctor
    diagnosis = models.TextField(blank=True)
    treatment = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    risk_level = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], blank=True)
    
    # FHIR-compliant fields
    identifier_system = models.CharField(max_length=255, default="urn:panacare:appointment", blank=True)
    healthcare_facility = models.ForeignKey(HealthCare, on_delete=models.SET_NULL, null=True, blank=True, related_name='appointments')
    
    # Metadata fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Appointment"
        verbose_name_plural = "Appointments"
        ordering = ['-appointment_date', '-start_time']
    
    def __str__(self):
        return f"{self.patient.user.get_full_name()} with Dr. {self.doctor.user.get_full_name()} on {self.appointment_date} at {self.start_time}"
    
    def to_fhir_json(self):
        """Return FHIR-compliant representation as Appointment resource"""
        from django.utils import timezone
        
        # Create a datetime that combines the date and time fields
        start_datetime = timezone.make_aware(
            timezone.datetime.combine(self.appointment_date, self.start_time)
        )
        end_datetime = timezone.make_aware(
            timezone.datetime.combine(self.appointment_date, self.end_time)
        )
        
        fhir_json = {
            "resourceType": "Appointment",
            "id": str(self.id),
            "identifier": [
                {
                    "system": self.identifier_system,
                    "value": str(self.id)
                }
            ],
            "status": self.status,
            "appointmentType": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0276",
                        "code": self.appointment_type,
                        "display": dict(self._meta.get_field('appointment_type').choices).get(self.appointment_type)
                    }
                ]
            },
            "reason": [
                {
                    "text": self.reason
                }
            ] if self.reason else [],
            "start": start_datetime.isoformat(),
            "end": end_datetime.isoformat(),
            "participant": [
                {
                    "actor": {
                        "reference": f"Patient/{self.patient.id}",
                        "display": self.patient.user.get_full_name() or self.patient.user.email
                    },
                    "status": "accepted"
                },
                {
                    "actor": {
                        "reference": f"Practitioner/{self.doctor.id}",
                        "display": f"Dr. {self.doctor.user.get_full_name()}"
                    },
                    "status": "accepted"
                }
            ]
        }
        
        # Add healthcare service location if available
        if self.healthcare_facility:
            fhir_json["participant"].append({
                "actor": {
                    "reference": f"Organization/{self.healthcare_facility.id}",
                    "display": self.healthcare_facility.name
                },
                "status": "accepted"
            })
            
        return fhir_json


class AppointmentDocument(models.Model):
    """
    Documents related to an appointment (prescriptions, lab results, etc.)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='documents')
    
    # Document details
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='appointment_documents/%Y/%m/%d/')
    document_type = models.CharField(max_length=50, choices=[
        ('prescription', 'Prescription'),
        ('lab_result', 'Lab Result'),
        ('imaging', 'Imaging Result'),
        ('referral', 'Referral'),
        ('note', 'Clinical Note'),
        ('other', 'Other')
    ])
    description = models.TextField(blank=True)
    
    # Metadata
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='uploaded_documents'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Appointment Document"
        verbose_name_plural = "Appointment Documents"
        
    def __str__(self):
        return f"{self.title} - {self.appointment}"


class Consultation(models.Model):
    """
    Video consultation session tied to an appointment
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='consultation')
    
    # Consultation status
    status = models.CharField(max_length=20, choices=[
        ('scheduled', 'Scheduled'),
        ('in-progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('missed', 'Missed'),
    ], default='scheduled')
    
    # Consultation details
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
    # Session details
    session_id = models.CharField(max_length=255, blank=True)  # External video session ID
    recording_url = models.URLField(max_length=255, blank=True)
    
    # Twilio Video specific fields
    twilio_room_name = models.CharField(max_length=255, blank=True)
    twilio_room_sid = models.CharField(max_length=255, blank=True)
    doctor_token = models.TextField(blank=True)  # To store doctor's Twilio access token
    patient_token = models.TextField(blank=True)  # To store patient's Twilio access token
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Consultation"
        verbose_name_plural = "Consultations"
        
    def __str__(self):
        return f"Consultation for {self.appointment}"


class ConsultationChat(models.Model):
    """
    Chat messages within a consultation
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='chat_messages')
    
    # Message content
    message = models.TextField()
    
    # Sender info
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_chat_messages')
    is_doctor = models.BooleanField(default=False, help_text="Whether the sender is a doctor")
    
    # Message status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Consultation Chat Message"
        verbose_name_plural = "Consultation Chat Messages"
        ordering = ['created_at']
        
    def __str__(self):
        return f"Message from {self.sender.get_full_name()} in {self.consultation}"


class Package(models.Model):
    """
    Subscription package for patients
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField()
    
    # Features
    consultation_count = models.PositiveIntegerField(default=0)
    max_doctors = models.PositiveIntegerField(default=1)
    priority_support = models.BooleanField(default=False)
    access_to_resources = models.BooleanField(default=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Package"
        verbose_name_plural = "Packages"
        
    def __str__(self):
        return self.name


class PatientSubscription(models.Model):
    """
    Patient subscription to a package
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('users.Patient', on_delete=models.CASCADE, related_name='subscriptions')
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    
    # Subscription details
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('pending', 'Pending'),
    ], default='active')
    
    # Usage tracking
    consultations_used = models.PositiveIntegerField(default=0)
    
    # Payment details (basic)
    payment_reference = models.CharField(max_length=255, blank=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Patient Subscription"
        verbose_name_plural = "Patient Subscriptions"
        
    def __str__(self):
        return f"{self.patient.user.get_full_name()} - {self.package.name}"


class Resource(models.Model):
    """
    Educational resources for patients
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    content_type = models.CharField(max_length=20, choices=[
        ('article', 'Article'),
        ('video', 'Video'),
        ('pdf', 'PDF'),
        ('link', 'External Link'),
        ('other', 'Other'),
    ])
    
    # Content
    file = models.FileField(upload_to='resources/', blank=True, null=True)
    url = models.URLField(max_length=255, blank=True)
    text_content = models.TextField(blank=True)
    
    # Access control
    is_password_protected = models.BooleanField(default=False)
    password_hash = models.CharField(max_length=255, blank=True)  # Hashed password
    
    # Resource categorization
    category = models.CharField(max_length=50, choices=[
        ('general', 'General Health'),
        ('nutrition', 'Nutrition'),
        ('fitness', 'Fitness'),
        ('mental', 'Mental Health'),
        ('children', 'Children\'s Health'),
        ('chronic', 'Chronic Conditions'),
        ('prevention', 'Preventive Care'),
        ('other', 'Other'),
    ])
    tags = models.CharField(max_length=255, blank=True)  # Comma-separated tags
    
    # Publishing details
    author = models.ForeignKey(
        'doctors.Doctor', on_delete=models.SET_NULL, null=True, blank=True, related_name='resources'
    )
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_resources'
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Resource"
        verbose_name_plural = "Resources"
        
    def __str__(self):
        return self.title


class DoctorRating(models.Model):
    """
    Doctor ratings by patients
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, related_name='ratings')
    patient = models.ForeignKey('users.Patient', on_delete=models.CASCADE, related_name='doctor_ratings')
    
    # Rating details
    rating = models.PositiveSmallIntegerField(choices=[
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ])
    review = models.TextField(blank=True)
    
    # Metadata
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Doctor Rating"
        verbose_name_plural = "Doctor Ratings"
        unique_together = ('doctor', 'patient')
        
    def __str__(self):
        return f"{self.patient.user.get_full_name()} rated Dr. {self.doctor.user.get_full_name()} {self.rating} stars"


class Article(models.Model):
    """
    Articles created by doctors and read by both doctors and patients
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    content = models.TextField()
    summary = models.TextField(blank=True)
    
    # Article metadata
    author = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, related_name='articles')
    category = models.CharField(max_length=50, choices=[
        ('general', 'General Health'),
        ('nutrition', 'Nutrition'),
        ('fitness', 'Fitness'),
        ('mental', 'Mental Health'),
        ('children', 'Children\'s Health'),
        ('chronic', 'Chronic Conditions'),
        ('prevention', 'Preventive Care'),
        ('research', 'Medical Research'),
        ('other', 'Other'),
    ])
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags")
    
    # Featured image
    featured_image = models.ImageField(upload_to='articles/images/%Y/%m/', blank=True, null=True)
    
    # Approval status
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='approved_articles'
    )
    approval_date = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    
    # Publication status
    is_published = models.BooleanField(default=False)
    publish_date = models.DateTimeField(null=True, blank=True)
    
    # Stats
    view_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ['-created_at']
        
    def __str__(self):
        return self.title


class ArticleComment(models.Model):
    """
    Comments on articles by doctors and patients
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    
    # Comment content
    content = models.TextField()
    
    # Author - can be either a doctor or a patient
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='article_comments')
    is_doctor = models.BooleanField(default=False, help_text="Whether the commenter is a doctor")
    
    # Reply structure - limited to one level
    parent_comment = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, blank=True, 
        related_name='replies'
    )
    
    # Likes
    like_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Article Comment"
        verbose_name_plural = "Article Comments"
        ordering = ['created_at']
        
    def __str__(self):
        return f"Comment by {self.user.get_full_name()} on {self.article.title}"


class ArticleCommentLike(models.Model):
    """
    Likes on article comments by users
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    comment = models.ForeignKey(ArticleComment, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comment_likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Comment Like"
        verbose_name_plural = "Comment Likes"
        unique_together = ('comment', 'user')
        
    def __str__(self):
        return f"{self.user.get_full_name()} liked comment on {self.comment.article.title}"
