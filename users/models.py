from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
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
        message = render_to_string('users/activation_email.html', {
            'user': self,
            'activation_url': activation_url,
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

class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer')
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email}'s Profile"
