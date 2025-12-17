from django.db import models
from django.contrib.auth import get_user_model

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
