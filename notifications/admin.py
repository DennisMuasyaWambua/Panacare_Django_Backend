from django.contrib import admin
from .models import FCMDevice, NotificationHistory, NotificationPreferences, TopicSubscription


@admin.register(FCMDevice)
class FCMDeviceAdmin(admin.ModelAdmin):
    list_display = ['user', 'platform', 'active', 'token_preview', 'created_at']
    list_filter = ['platform', 'active', 'created_at']
    search_fields = ['user__username', 'user__email', 'token']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def token_preview(self, obj):
        return f"{obj.token[:30]}..."
    token_preview.short_description = 'Token Preview'
    
    actions = ['deactivate_devices', 'activate_devices']
    
    def deactivate_devices(self, request, queryset):
        updated = queryset.update(active=False)
        self.message_user(request, f'{updated} devices deactivated.')
    deactivate_devices.short_description = 'Deactivate selected devices'
    
    def activate_devices(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, f'{updated} devices activated.')
    activate_devices.short_description = 'Activate selected devices'


@admin.register(NotificationHistory)
class NotificationHistoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'notification_type', 'status', 'is_read', 'created_at']
    list_filter = ['notification_type', 'status', 'is_read', 'created_at']
    search_fields = ['user__username', 'user__email', 'title', 'body']
    readonly_fields = ['id', 'created_at', 'read_at']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'title', 'body', 'notification_type')
        }),
        ('Status', {
            'fields': ('status', 'is_read', 'read_at')
        }),
        ('Metadata', {
            'fields': ('data', 'sent_by', 'created_at')
        }),
    )
    
    actions = ['mark_as_read']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = 'Mark selected notifications as read'


@admin.register(NotificationPreferences)
class NotificationPreferencesAdmin(admin.ModelAdmin):
    list_display = ['user', 'push_appointments', 'push_consultations', 'push_emergency', 'quiet_hours_enabled']
    list_filter = ['push_emergency', 'quiet_hours_enabled', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Push Notifications', {
            'fields': (
                'push_appointments', 'push_consultations', 'push_payments',
                'push_subscriptions', 'push_articles', 'push_emergency',
                'push_announcements', 'push_reminders', 'push_general'
            )
        }),
        ('Email Notifications', {
            'fields': (
                'email_appointments', 'email_consultations', 'email_payments',
                'email_subscriptions', 'email_articles', 'email_emergency',
                'email_announcements', 'email_reminders', 'email_general'
            ),
            'classes': ('collapse',)
        }),
        ('SMS Notifications', {
            'fields': (
                'sms_appointments', 'sms_consultations', 'sms_payments',
                'sms_subscriptions', 'sms_articles', 'sms_emergency',
                'sms_announcements', 'sms_reminders', 'sms_general'
            ),
            'classes': ('collapse',)
        }),
        ('Quiet Hours', {
            'fields': ('quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TopicSubscription)
class TopicSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'topic', 'topic_display_name', 'subscribed', 'created_at']
    list_filter = ['topic', 'subscribed', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def topic_display_name(self, obj):
        return obj.get_topic_display()
    topic_display_name.short_description = 'Topic Name'
    
    actions = ['subscribe_to_topic', 'unsubscribe_from_topic']
    
    def subscribe_to_topic(self, request, queryset):
        updated = queryset.update(subscribed=True)
        self.message_user(request, f'{updated} subscriptions activated.')
    subscribe_to_topic.short_description = 'Subscribe to topic'
    
    def unsubscribe_from_topic(self, request, queryset):
        updated = queryset.update(subscribed=False)
        self.message_user(request, f'{updated} subscriptions deactivated.')
    unsubscribe_from_topic.short_description = 'Unsubscribe from topic'
