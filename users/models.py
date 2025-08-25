from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
import uuid

class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.CharField(max_length=255, blank=True)
    roles = models.ManyToManyField(Role, related_name='users')
    is_verified = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email
    
    def send_activation_email(self, domain):
        """
        Send an activation email to the user
        """
        import logging
        logger = logging.getLogger(__name__)
        
        uid = urlsafe_base64_encode(force_bytes(self.pk))
        token = default_token_generator.make_token(self)
        
        # Use https if not localhost/127.0.0.1
        protocol = 'http'
        if domain not in ['localhost', '127.0.0.1'] and not domain.startswith('192.168.'):
            protocol = 'https'
            
        activation_url = f"{protocol}://{domain}/api/users/activate/{uid}/{token}/"
        
        subject = 'Activate Your Panacare Account'
        logo_url = f"{protocol}://{domain}/static/images/logo.jpg"
        message = render_to_string('users/activation_email.html', {
            'user': self,
            'activation_url': activation_url,
            'logo_url': logo_url,
        })
        
        # Use DEFAULT_FROM_EMAIL as fallback if EMAIL_HOST_USER is empty
        from_email = settings.EMAIL_HOST_USER or settings.DEFAULT_FROM_EMAIL or 'noreply@panacare.com'
        
        # Log email sending attempt
        logger.info(f"Attempting to send activation email to {self.email} from {from_email}")
        logger.info(f"Email settings: HOST={settings.EMAIL_HOST}, PORT={settings.EMAIL_PORT}, TLS={settings.EMAIL_USE_TLS}")
        
        try:
            result = send_mail(
                subject,
                message,
                from_email,
                [self.email],
                html_message=message,
                fail_silently=False,
            )
            logger.info(f"Email sending result: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            raise

class Patient(models.Model):
    """
    Patient model (maps to FHIR Patient resource)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient')
    
    # Basic FHIR Patient fields
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[
        ('male', 'Male'), 
        ('female', 'Female'), 
        ('other', 'Other'),
        ('unknown', 'Unknown')
    ], blank=True)
    active = models.BooleanField(default=True)
    
    # Medical information
    blood_type = models.CharField(max_length=5, blank=True, choices=[
        ('A+', 'A Positive'),
        ('A-', 'A Negative'),
        ('B+', 'B Positive'),
        ('B-', 'B Negative'),
        ('AB+', 'AB Positive'),
        ('AB-', 'AB Negative'),
        ('O+', 'O Positive'),
        ('O-', 'O Negative'),
        ('', 'Unknown')
    ])
    height_cm = models.PositiveIntegerField(null=True, blank=True, help_text="Height in centimeters")
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Weight in kilograms")
    allergies = models.TextField(blank=True, help_text="Known allergies")
    medical_conditions = models.TextField(blank=True, help_text="Pre-existing medical conditions")
    medications = models.TextField(blank=True, help_text="Current medications")
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    
    # Additional FHIR-compliant fields
    identifier_system = models.CharField(max_length=255, default="urn:panacare:patient", blank=True)
    marital_status = models.CharField(max_length=50, blank=True, choices=[
        ('M', 'Married'),
        ('S', 'Single'),
        ('D', 'Divorced'),
        ('W', 'Widowed'),
        ('U', 'Unknown')
    ])
    language = models.CharField(max_length=50, blank=True, default="en")
    
    # Insurance information
    insurance_provider = models.CharField(max_length=100, blank=True)
    insurance_policy_number = models.CharField(max_length=50, blank=True)
    insurance_group_number = models.CharField(max_length=50, blank=True)
    
    # Metadata fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Patient"
        verbose_name_plural = "Patients"
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email}'s Patient Record"
    
    def to_fhir_json(self):
        """Return FHIR-compliant representation of patient"""
        patient_json = {
            "resourceType": "Patient",
            "id": str(self.id),
            "identifier": [
                {
                    "system": self.identifier_system,
                    "value": str(self.id)
                }
            ],
            "active": self.active,
            "name": [
                {
                    "use": "official",
                    "family": self.user.last_name,
                    "given": [self.user.first_name]
                }
            ],
            "telecom": [
                {
                    "system": "email",
                    "value": self.user.email,
                    "use": "home"
                },
                {
                    "system": "phone",
                    "value": self.user.phone_number,
                    "use": "mobile"
                } if self.user.phone_number else None
            ],
            "gender": self.gender or "unknown",
            "birthDate": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "address": [
                {
                    "use": "home",
                    "line": [self.user.address],
                    "text": self.user.address
                }
            ] if self.user.address else [],
            "maritalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
                        "code": self.marital_status or "U"
                    }
                ]
            },
            "communication": [
                {
                    "language": {
                        "coding": [
                            {
                                "system": "urn:ietf:bcp:47",
                                "code": self.language
                            }
                        ]
                    },
                    "preferred": True
                }
            ]
        }
        
        # Add insurance information if available
        if self.insurance_provider or self.insurance_policy_number:
            patient_json["extension"] = patient_json.get("extension", []) + [
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/patient-insurance",
                    "extension": [
                        {
                            "url": "provider",
                            "valueString": self.insurance_provider
                        },
                        {
                            "url": "policy-number",
                            "valueString": self.insurance_policy_number
                        },
                        {
                            "url": "group-number",
                            "valueString": self.insurance_group_number
                        }
                    ]
                }
            ]
            
        # Add emergency contact if available
        if self.emergency_contact_name:
            patient_json["contact"] = [
                {
                    "relationship": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/v2-0131",
                                    "code": "C",
                                    "display": "Emergency Contact"
                                }
                            ],
                            "text": self.emergency_contact_relationship
                        }
                    ],
                    "name": {
                        "text": self.emergency_contact_name
                    },
                    "telecom": [
                        {
                            "system": "phone",
                            "value": self.emergency_contact_phone,
                            "use": "mobile"
                        }
                    ] if self.emergency_contact_phone else []
                }
            ]
            
        # Add vital signs and medical information
        if self.height_cm or self.weight_kg or self.blood_type:
            height_weight_extension = []
            
            if self.height_cm:
                height_weight_extension.append({
                    "url": "height",
                    "valueQuantity": {
                        "value": self.height_cm,
                        "unit": "cm",
                        "system": "http://unitsofmeasure.org",
                        "code": "cm"
                    }
                })
                
            if self.weight_kg:
                height_weight_extension.append({
                    "url": "weight",
                    "valueQuantity": {
                        "value": float(self.weight_kg),
                        "unit": "kg",
                        "system": "http://unitsofmeasure.org",
                        "code": "kg"
                    }
                })
                
            if self.blood_type:
                height_weight_extension.append({
                    "url": "blood-type",
                    "valueCodeableConcept": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0005",
                                "code": self.blood_type,
                                "display": dict(self._meta.get_field('blood_type').choices).get(self.blood_type)
                            }
                        ]
                    }
                })
                
            if height_weight_extension:
                patient_json["extension"] = patient_json.get("extension", []) + [
                    {
                        "url": "http://hl7.org/fhir/StructureDefinition/patient-vitalsigns",
                        "extension": height_weight_extension
                    }
                ]
                
        # Add allergies, medical conditions and medications if available  
        if self.allergies or self.medical_conditions or self.medications:
            medical_info_extension = []
            
            if self.allergies:
                medical_info_extension.append({
                    "url": "allergies",
                    "valueString": self.allergies
                })
                
            if self.medical_conditions:
                medical_info_extension.append({
                    "url": "medical-conditions",
                    "valueString": self.medical_conditions
                })
                
            if self.medications:
                medical_info_extension.append({
                    "url": "medications",
                    "valueString": self.medications
                })
                
            if medical_info_extension:
                patient_json["extension"] = patient_json.get("extension", []) + [
                    {
                        "url": "http://hl7.org/fhir/StructureDefinition/patient-medicalInformation",
                        "extension": medical_info_extension
                    }
                ]
        
        return patient_json

# Signal to create a Patient profile when a user is assigned the patient role
@receiver(m2m_changed, sender=User.roles.through)
def create_patient_profile(sender, instance, action, pk_set, **kwargs):
    """
    Signal handler to create a Patient profile when a user is assigned the patient role.
    """
    if action == 'post_add':
        # Check if any of the newly added roles is 'patient'
        patient_role_exists = Role.objects.filter(pk__in=pk_set, name='patient').exists()
        
        if patient_role_exists:
            # Create a Patient profile if it doesn't exist
            Patient.objects.get_or_create(user=instance)

class AuditLog(models.Model):
    """
    Model to track user activities and audit trail for security and compliance
    """
    ACTIVITY_CHOICES = [
        ('login', 'Logged In'),
        ('logout', 'Logged Out'),
        ('register', 'User Registration'),
        ('profile_update', 'Profile Updated'),
        ('password_change', 'Password Changed'),
        ('appointment_create', 'Appointment Created'),
        ('appointment_update', 'Appointment Updated'),
        ('appointment_cancel', 'Appointment Cancelled'),
        ('consultation_start', 'Consultation Started'),
        ('consultation_end', 'Consultation Ended'),
        ('article_create', 'Article Created'),
        ('article_update', 'Article Updated'),
        ('article_approve', 'Article Approved'),
        ('article_reject', 'Article Rejected'),
        ('user_create', 'User Created'),
        ('user_update', 'User Updated'),
        ('user_delete', 'User Deleted'),
        ('role_assign', 'Role Assigned'),
        ('subscription_create', 'Subscription Created'),
        ('payment_process', 'Payment Processed'),
        ('data_export', 'Data Exported'),
        ('system_access', 'System Access'),
        ('api_access', 'API Access'),
        ('other', 'Other Activity'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('pending', 'Pending'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_logs')
    username = models.CharField(max_length=150, help_text="Username at time of activity")
    activity = models.CharField(max_length=50, choices=ACTIVITY_CHOICES, help_text="Type of activity performed")
    email_address = models.EmailField(help_text="Email address at time of activity")
    role = models.CharField(max_length=100, help_text="User roles at time of activity")
    time_spent = models.DurationField(null=True, blank=True, help_text="Time spent on activity")
    date_joined = models.DateTimeField(help_text="When the user joined the system")
    last_active = models.DateTimeField(auto_now=True, help_text="Last activity timestamp")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Additional fields for context
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address of the user")
    user_agent = models.TextField(blank=True, help_text="User agent string")
    session_id = models.CharField(max_length=255, blank=True, help_text="Session identifier")
    details = models.JSONField(default=dict, blank=True, help_text="Additional activity details")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['activity', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.username} - {self.get_activity_display()} at {self.created_at}"
    
    @property
    def formatted_time_spent(self):
        """Return formatted time spent as human readable string"""
        if not self.time_spent:
            return "N/A"
        
        total_seconds = int(self.time_spent.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return f"{total_seconds}s"