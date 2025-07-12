from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Appointment, Consultation
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Appointment)
def create_consultation_for_appointment(sender, instance, created, **kwargs):
    """
    Automatically create a consultation when an appointment is booked.
    
    This signal handler creates a consultation with 'scheduled' status
    whenever a new appointment is created.
    """
    if created:  # Only for new appointments
        try:
            # Check if consultation already exists to avoid duplicates
            if not hasattr(instance, 'consultation'):
                consultation = Consultation.objects.create(
                    appointment=instance,
                    status='scheduled'
                )
                logger.info(f"Auto-created consultation {consultation.id} for appointment {instance.id}")
            else:
                logger.info(f"Consultation already exists for appointment {instance.id}")
        except Exception as e:
            logger.error(f"Failed to create consultation for appointment {instance.id}: {str(e)}")