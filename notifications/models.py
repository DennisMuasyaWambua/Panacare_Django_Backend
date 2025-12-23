from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class FCMDevice(models.Model):
    """Store FCM device tokens for push notifications"""
    
    PLATFORM_CHOICES = [
        ('android', 'Android'),
        ('ios', 'iOS'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='fcm_devices'
    )
    token = models.CharField(max_length=255, unique=True, db_index=True)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fcm_devices'
        indexes = [
            models.Index(fields=['user', 'active']),
        ]
        verbose_name = 'FCM Device'
        verbose_name_plural = 'FCM Devices'
    
    def __str__(self):
        return f"{self.user.username} - {self.platform} - {self.token[:20]}..."


class NotificationHistory(models.Model):
    """Store notification history for users"""
    
    NOTIFICATION_TYPES = [
        ('appointment', 'Appointment'),
        ('consultation', 'Consultation'),
        ('payment', 'Payment'),
        ('subscription', 'Subscription'),
        ('article', 'Article'),
        ('emergency', 'Emergency'),
        ('announcement', 'Announcement'),
        ('reminder', 'Reminder'),
        ('general', 'General'),
    ]
    
    NOTIFICATION_STATUS = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    body = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='general')
    data = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=NOTIFICATION_STATUS, default='sent')
    is_read = models.BooleanField(default=False)
    sent_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='sent_notifications'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'notification_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Notification History'
        verbose_name_plural = 'Notification History'
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class NotificationPreferences(models.Model):
    """Store user notification preferences"""
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='notification_preferences'
    )
    
    # Push notification preferences
    push_appointments = models.BooleanField(default=True)
    push_consultations = models.BooleanField(default=True)
    push_payments = models.BooleanField(default=True)
    push_subscriptions = models.BooleanField(default=True)
    push_articles = models.BooleanField(default=True)
    push_emergency = models.BooleanField(default=True)
    push_announcements = models.BooleanField(default=True)
    push_reminders = models.BooleanField(default=True)
    push_general = models.BooleanField(default=True)
    
    # Email notification preferences (for future use)
    email_appointments = models.BooleanField(default=False)
    email_consultations = models.BooleanField(default=False)
    email_payments = models.BooleanField(default=True)
    email_subscriptions = models.BooleanField(default=True)
    email_articles = models.BooleanField(default=False)
    email_emergency = models.BooleanField(default=True)
    email_announcements = models.BooleanField(default=False)
    email_reminders = models.BooleanField(default=True)
    email_general = models.BooleanField(default=False)
    
    # SMS notification preferences (for future use)
    sms_appointments = models.BooleanField(default=False)
    sms_consultations = models.BooleanField(default=False)
    sms_payments = models.BooleanField(default=False)
    sms_subscriptions = models.BooleanField(default=False)
    sms_articles = models.BooleanField(default=False)
    sms_emergency = models.BooleanField(default=True)
    sms_announcements = models.BooleanField(default=False)
    sms_reminders = models.BooleanField(default=True)
    sms_general = models.BooleanField(default=False)
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(default='22:00')
    quiet_hours_end = models.TimeField(default='08:00')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_preferences'
        verbose_name = 'Notification Preferences'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"{self.user.username} - Notification Preferences"
    
    def can_send_push_notification(self, notification_type):
        """Check if push notification is allowed for given type"""
        field_name = f'push_{notification_type}'
        return getattr(self, field_name, True)


class TopicSubscription(models.Model):
    """Store user topic subscriptions for broadcast notifications"""
    
    TOPIC_CHOICES = [
        ('all_users', 'All Users'),
        ('doctors', 'Doctors'),
        ('patients', 'Patients'),
        ('admins', 'Administrators'),
        ('emergencies', 'Emergency Alerts'),
        ('announcements', 'General Announcements'),
        ('health_tips', 'Health Tips'),
        ('system_updates', 'System Updates'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topic_subscriptions')
    topic = models.CharField(max_length=50, choices=TOPIC_CHOICES)
    subscribed = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'topic_subscriptions'
        unique_together = ['user', 'topic']
        indexes = [
            models.Index(fields=['topic', 'subscribed']),
        ]
        verbose_name = 'Topic Subscription'
        verbose_name_plural = 'Topic Subscriptions'
    
    def __str__(self):
        status = "Subscribed" if self.subscribed else "Unsubscribed"
        return f"{self.user.username} - {self.topic} ({status})"
