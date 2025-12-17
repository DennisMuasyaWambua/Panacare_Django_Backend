from django.contrib import admin
from .models import FCMDevice


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
