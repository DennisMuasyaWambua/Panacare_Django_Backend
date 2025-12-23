from rest_framework import serializers
from .models import FCMDevice, NotificationHistory, NotificationPreferences, TopicSubscription
from users.serializers import UserSerializer


class FCMDeviceSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = FCMDevice
        fields = ['id', 'user', 'token', 'platform', 'active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationHistorySerializer(serializers.ModelSerializer):
    sent_by = UserSerializer(read_only=True)
    
    class Meta:
        model = NotificationHistory
        fields = [
            'id', 'title', 'body', 'notification_type', 'data', 'status', 
            'is_read', 'sent_by', 'created_at', 'read_at'
        ]
        read_only_fields = ['id', 'created_at', 'read_at']


class NotificationHistoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating notification history entries"""
    
    class Meta:
        model = NotificationHistory
        fields = ['title', 'body', 'notification_type', 'data']


class NotificationPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreferences
        fields = [
            'push_appointments', 'push_consultations', 'push_payments', 
            'push_subscriptions', 'push_articles', 'push_emergency', 
            'push_announcements', 'push_reminders', 'push_general',
            'email_appointments', 'email_consultations', 'email_payments', 
            'email_subscriptions', 'email_articles', 'email_emergency', 
            'email_announcements', 'email_reminders', 'email_general',
            'sms_appointments', 'sms_consultations', 'sms_payments', 
            'sms_subscriptions', 'sms_articles', 'sms_emergency', 
            'sms_announcements', 'sms_reminders', 'sms_general',
            'quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class TopicSubscriptionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    topic_display = serializers.CharField(source='get_topic_display', read_only=True)
    
    class Meta:
        model = TopicSubscription
        fields = ['id', 'user', 'topic', 'topic_display', 'subscribed', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SendNotificationSerializer(serializers.Serializer):
    """Serializer for sending notifications"""
    
    RECIPIENT_TYPES = [
        ('user', 'Specific User'),
        ('users', 'Multiple Users'),
        ('role', 'User Role'),
        ('topic', 'Topic Subscribers'),
        ('all', 'All Users'),
    ]
    
    title = serializers.CharField(max_length=255)
    body = serializers.CharField()
    notification_type = serializers.ChoiceField(
        choices=NotificationHistory.NOTIFICATION_TYPES, 
        default='general'
    )
    data = serializers.JSONField(default=dict, required=False)
    
    recipient_type = serializers.ChoiceField(choices=RECIPIENT_TYPES)
    
    # For specific user
    user_id = serializers.UUIDField(required=False, allow_null=True)
    
    # For multiple users
    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=False
    )
    
    # For role-based sending
    role = serializers.ChoiceField(
        choices=[('doctor', 'Doctors'), ('patient', 'Patients'), ('admin', 'Admins')],
        required=False,
        allow_null=True
    )
    
    # For topic-based sending
    topic = serializers.ChoiceField(
        choices=TopicSubscription.TOPIC_CHOICES,
        required=False,
        allow_null=True
    )
    
    # Whether to save to notification history
    save_to_history = serializers.BooleanField(default=True)
    
    def validate(self, data):
        recipient_type = data.get('recipient_type')
        
        if recipient_type == 'user' and not data.get('user_id'):
            raise serializers.ValidationError("user_id is required when recipient_type is 'user'")
        
        if recipient_type == 'users' and not data.get('user_ids'):
            raise serializers.ValidationError("user_ids is required when recipient_type is 'users'")
        
        if recipient_type == 'role' and not data.get('role'):
            raise serializers.ValidationError("role is required when recipient_type is 'role'")
        
        if recipient_type == 'topic' and not data.get('topic'):
            raise serializers.ValidationError("topic is required when recipient_type is 'topic'")
        
        return data


class BulkNotificationResultSerializer(serializers.Serializer):
    """Serializer for bulk notification results"""
    
    total_recipients = serializers.IntegerField()
    notifications_sent = serializers.IntegerField()
    notifications_failed = serializers.IntegerField()
    success_rate = serializers.FloatField()
    details = serializers.JSONField()