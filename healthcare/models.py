from django.db import models
import uuid
from django.conf import settings
from datetime import timedelta
from django.utils import timezone

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
    # doctors = models.ManyToManyField('doctors.Doctor', related_name='healthcare_facilities', blank=True)
    
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

# Alias for compatibility
Healthcare = HealthCare

# Commented out other models for testing
class EncounterStatus(models.TextChoices):
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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('users.Patient', on_delete=models.CASCADE, related_name='doctor_assignments')
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, related_name='patient_assignments')
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('patient', 'doctor')
       
    def __str__(self):
        return f"Patient: {self.patient.user.get_full_name()} - Doctor: {self.doctor.user.get_full_name()}"
    
#     def to_fhir_json(self):
#         from django.utils import timezone
#         status = self.status
#         if not status:
#             status = EncounterStatus.IN_PROGRESS if self.is_active else EncounterStatus.FINISHED
#         period = {}
#         if self.actual_start:
#             period["start"] = self.actual_start.isoformat()
#         elif self.scheduled_start:
#             period["start"] = self.scheduled_start.isoformat()
#         else:
#             period["start"] = self.created_at.isoformat()
#         if self.actual_end:
#             period["end"] = self.actual_end.isoformat()
#         elif not self.is_active:
#             period["end"] = self.updated_at.isoformat()
#         fhir_json = {
#             "resourceType": "Encounter",
#             "id": str(self.id),
#             "identifier": [
#                 {
#                     "system": self.identifier_system,
#                     "value": str(self.id)
#                 }
#             ],
#             "status": status,
#             "class": {
#                 "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
#                 "code": self.encounter_type,
#                 "display": self.get_encounter_type_display()
#             },
#             "subject": {
#                 "reference": f"Patient/{self.patient.id}",
#                 "display": self.patient.user.get_full_name() or self.patient.user.username
#             },
#             "participant": [
#                 {
#                     "individual": {
#                         "reference": f"Practitioner/{self.doctor.id}",
#                         "display": self.doctor.user.get_full_name() or self.doctor.user.username
#                     },
#                     "type": [
#                         {
#                             "coding": [
#                                 {
#                                     "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
#                                     "code": "PPRF",
#                                     "display": "Primary performer"
#                                 }
#                             ]
#                         }
#                     ]
#                 }
#             ],
#             "period": period
#         }
#         if self.reason or self.notes:
#             fhir_json["reasonCode"] = [
#                 {
#                     "text": self.reason or self.notes
#                 }
#             ]
#         if self.healthcare_facility:
#             fhir_json["serviceProvider"] = {
#                 "reference": f"Organization/{self.healthcare_facility.id}",
#                 "display": self.healthcare_facility.name
#             }
#         return fhir_json


# class DoctorAvailability(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, related_name='availabilities')
#     day_of_week = models.IntegerField(choices=[
#         (0, 'Monday'),
#         (1, 'Tuesday'),
#         (2, 'Wednesday'),
#         (3, 'Thursday'),
#         (4, 'Friday'),
#         (5, 'Saturday'),
#         (6, 'Sunday'),
#     ])
#     start_time = models.TimeField()
#     end_time = models.TimeField()
#     is_recurring = models.BooleanField(default=True)
#     specific_date = models.DateField(null=True, blank=True)
#     is_available = models.BooleanField(default=True)
#     notes = models.TextField(blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     class Meta:
#         verbose_name = "Doctor Availability"
#         verbose_name_plural = "Doctor Availabilities"
       
#     def __str__(self):
#         day_name = dict(self._meta.get_field('day_of_week').choices).get(self.day_of_week)
#         if self.specific_date:
#             return f"Dr. {self.doctor.user.get_full_name()} available on {self.specific_date.strftime('%Y-%m-%d')} from {self.start_time} to {self.end_time}"
#         return f"Dr. {self.doctor.user.get_full_name()} available on {day_name}s from {self.start_time} to {self.end_time}"


class AppointmentStatus(models.TextChoices):
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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('users.Patient', on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
       max_length=20,
       choices=AppointmentStatus.choices,
       default=AppointmentStatus.BOOKED
    )
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
    diagnosis = models.TextField(blank=True)
    treatment = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    risk_level = models.CharField(max_length=20, choices=[
       ('low', 'Low'),
       ('medium', 'Medium'),
       ('high', 'High'),
       ('critical', 'Critical'),
    ], blank=True)
    identifier_system = models.CharField(max_length=255, default="urn:panacare:appointment", blank=True)
    healthcare_facility = models.ForeignKey(HealthCare, on_delete=models.SET_NULL, null=True, blank=True, related_name='appointments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
       verbose_name = "Appointment"
       verbose_name_plural = "Appointments"
       ordering = ['-appointment_date', '-start_time']
    
    def __str__(self):
       return f"{self.patient.user.get_full_name()} with Dr. {self.doctor.user.get_full_name()} on {self.appointment_date} at {self.start_time}"
    
    def to_fhir_json(self):
       from django.utils import timezone
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
       if self.healthcare_facility:
           fhir_json["participant"].append({
               "actor": {
                   "reference": f"Organization/{self.healthcare_facility.id}",
                   "display": self.healthcare_facility.name
               },
               "status": "accepted"
           })
       return fhir_json


# class AppointmentDocument(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='documents')
#     title = models.CharField(max_length=255)
#     file = models.FileField(upload_to='appointment_documents/%Y/%m/%d/')
#     document_type = models.CharField(max_length=50, choices=[
#         ('prescription', 'Prescription'),
#         ('lab_result', 'Lab Result'),
#         ('imaging', 'Imaging Result'),
#         ('referral', 'Referral'),
#         ('note', 'Clinical Note'),
#         ('other', 'Other')
#     ])
#     description = models.TextField(blank=True)
#     uploaded_by = models.ForeignKey(
#         settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='uploaded_documents'
#     )
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     class Meta:
#         verbose_name = "Appointment Document"
#         verbose_name_plural = "Appointment Documents"
       
#     def __str__(self):
#         return f"{self.title} - {self.appointment}"


class Consultation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='consultation')
    status = models.CharField(max_length=20, choices=[
       ('scheduled', 'Scheduled'),
       ('in-progress', 'In Progress'),
       ('completed', 'Completed'),
       ('cancelled', 'Cancelled'),
       ('missed', 'Missed'),
    ], default='scheduled')
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    session_id = models.CharField(max_length=255, blank=True)
    recording_url = models.URLField(max_length=255, blank=True)
    twilio_room_name = models.CharField(max_length=255, blank=True)
    twilio_room_sid = models.CharField(max_length=255, blank=True)
    doctor_token = models.TextField(blank=True)
    patient_token = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
       verbose_name = "Consultation"
       verbose_name_plural = "Consultations"
      
    def __str__(self):
       return f"Consultation for {self.appointment}"


class ConsultationChat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='chat_messages')
    message = models.TextField()
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_chat_messages')
    is_doctor = models.BooleanField(default=False, help_text="Whether the sender is a doctor")
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
       verbose_name = "Consultation Chat Message"
       verbose_name_plural = "Consultation Chat Messages"
       ordering = ['created_at']
      
    def __str__(self):
       return f"Message from {self.sender.get_full_name()} in {self.consultation}"


# class Package(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     name = models.CharField(max_length=100)
#     description = models.TextField()
#     price = models.DecimalField(max_digits=10, decimal_places=2)
#     duration_days = models.PositiveIntegerField()
#     consultation_count = models.PositiveIntegerField(default=0)
#     max_doctors = models.PositiveIntegerField(default=1)
#     priority_support = models.BooleanField(default=False)
#     access_to_resources = models.BooleanField(default=True)
#     is_active = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     class Meta:
#         verbose_name = "Package"
#         verbose_name_plural = "Packages"
       
#     def __str__(self):
#         return self.name


# class PatientSubscription(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     patient = models.ForeignKey('users.Patient', on_delete=models.CASCADE, related_name='subscriptions')
#     package = models.ForeignKey(Package, on_delete=models.CASCADE)
#     start_date = models.DateField(auto_now_add=True)
#     end_date = models.DateField()
#     status = models.CharField(max_length=20, choices=[
#         ('active', 'Active'),
#         ('cancelled', 'Cancelled'),
#         ('expired', 'Expired'),
#         ('pending', 'Pending'),
#     ], default='active')
#     consultations_used = models.PositiveIntegerField(default=0)
#     payment_reference = models.CharField(max_length=255, blank=True)
#     payment_date = models.DateTimeField(auto_now_add=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     class Meta:
#         verbose_name = "Patient Subscription"
#         verbose_name_plural = "Patient Subscriptions"
       
#     def __str__(self):
#         return f"{self.patient.user.get_full_name()} - {self.package.name}"


# class Resource(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     title = models.CharField(max_length=255)
#     description = models.TextField()
#     content_type = models.CharField(max_length=20, choices=[
#         ('article', 'Article'),
#         ('video', 'Video'),
#         ('pdf', 'PDF'),
#         ('link', 'External Link'),
#         ('other', 'Other'),
#     ])
#     file = models.FileField(upload_to='resources/', blank=True, null=True)
#     url = models.URLField(max_length=255, blank=True)
#     text_content = models.TextField(blank=True)
#     is_password_protected = models.BooleanField(default=False)
#     password_hash = models.CharField(max_length=255, blank=True)
#     category = models.CharField(max_length=50, choices=[
#         ('general', 'General Health'),
#         ('nutrition', 'Nutrition'),
#         ('fitness', 'Fitness'),
#         ('mental', 'Mental Health'),
#         ('children', 'Children\'s Health'),
#         ('chronic', 'Chronic Conditions'),
#         ('prevention', 'Preventive Care'),
#         ('other', 'Other'),
#     ])
#     tags = models.CharField(max_length=255, blank=True)
#     author = models.ForeignKey(
#         'doctors.Doctor', on_delete=models.CASCADE, null=True, blank=True, related_name='resources'
#     )
#     is_approved = models.BooleanField(default=False)
#     approved_by = models.ForeignKey(
#         settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_resources'
#     )
#     is_active = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     class Meta:
#         verbose_name = "Resource"
#         verbose_name_plural = "Resources"
       
#     def __str__(self):
#         return self.title


class DoctorRating(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, related_name='ratings')
    patient = models.ForeignKey('users.Patient', on_delete=models.CASCADE, related_name='doctor_ratings')
    rating = models.PositiveSmallIntegerField(choices=[
       (1, '1 Star'),
       (2, '2 Stars'),
       (3, '3 Stars'),
       (4, '4 Stars'),
       (5, '5 Stars'),
    ])
    review = models.TextField(blank=True)
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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    content = models.TextField()
    summary = models.TextField(blank=True)
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
    tags = models.CharField(max_length=255, blank=True)
    featured_image = models.ImageField(upload_to='articles/images/%Y/%m/', blank=True, null=True)
    visibility = models.CharField(max_length=20, choices=[
        ('public', 'Public - Available to all users'),
        ('subscribers', 'Subscribers Only - Available to paying patients'),
        ('private', 'Private - Only visible to author and admins'),
    ], default='public')
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='approved_articles'
    )
    approval_date = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)
    publish_date = models.DateTimeField(null=True, blank=True)
    view_count = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    related_conditions = models.CharField(max_length=255, blank=True)
    reading_time = models.PositiveSmallIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ['-created_at']
        
    def __str__(self):
        return self.title


class ArticleComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='article_comments')
    is_doctor = models.BooleanField(default=False)
    parent_comment = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, blank=True, 
        related_name='replies'
    )
    like_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Article Comment"
        verbose_name_plural = "Article Comments"
        ordering = ['created_at']
        
    def __str__(self):
        return f"Comment by {self.user.get_full_name()} on {self.article.title}"


class ArticleCommentLike(models.Model):
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


class Package(models.Model):
    """
    Subscription package model
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField(help_text="Duration in days")
    consultation_limit = models.IntegerField(help_text="Number of consultations allowed")
    features = models.JSONField(default=dict, help_text="Additional features as JSON")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Package"
        verbose_name_plural = "Packages"
        ordering = ['price']
    
    def __str__(self):
        return f"{self.name} - ${self.price}"


class Payment(models.Model):
    """
    Payment model for tracking subscription payments
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('pesapal', 'Pesapal'),
        ('mpesa', 'M-Pesa'),
        ('card', 'Credit/Debit Card'),
        ('bank', 'Bank Transfer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=100, unique=True, help_text="Payment reference from payment gateway")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='pesapal')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    gateway_transaction_id = models.CharField(max_length=200, blank=True, null=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.reference} - {self.amount} {self.currency}"


class PatientSubscription(models.Model):
    """
    Patient subscription model
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('users.Patient', on_delete=models.CASCADE, related_name='subscriptions')
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='subscriptions')
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateField()
    end_date = models.DateField()
    consultations_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Patient Subscription"
        verbose_name_plural = "Patient Subscriptions"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient.user.get_full_name()} - {self.package.name}"
    
    @property
    def is_active(self):
        from django.utils import timezone
        return (self.status == 'active' and 
                self.start_date <= timezone.now().date() <= self.end_date)
    
    @property
    def consultations_remaining(self):
        return max(0, self.package.consultation_limit - self.consultations_used)


class DoctorAvailability(models.Model):
    """
    Doctor availability model for scheduling
    """
    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, related_name='availability')
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Doctor Availability"
        verbose_name_plural = "Doctor Availabilities"
        unique_together = ('doctor', 'weekday', 'start_time')
        ordering = ['weekday', 'start_time']
    
    def __str__(self):
        return f"Dr. {self.doctor.user.get_full_name()} - {self.get_weekday_display()} {self.start_time}-{self.end_time}"