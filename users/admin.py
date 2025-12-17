from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, Patient, CommunityHealthProvider, AuditLog

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff', 'is_verified', 'display_roles')
    list_filter = ('is_staff', 'is_superuser', 'is_verified', 'roles')
    
    def display_roles(self, obj):
        return ", ".join([role.name for role in obj.roles.all()])
    display_roles.short_description = 'Roles'
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number', 'address')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified', 'roles')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at', 'updated_at')

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('user', 'gender', 'date_of_birth', 'blood_type', 'active')
    list_filter = ('gender', 'blood_type', 'active')
    search_fields = ('user__email', 'user__username', 'user__first_name', 'user__last_name', 'medical_conditions', 'allergies')
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'active', 'date_of_birth', 'gender', 'marital_status', 'language')
        }),
        ('Medical Information', {
            'fields': ('blood_type', 'height_cm', 'weight_kg', 'allergies', 'medical_conditions', 'medications')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship')
        }),
        ('Insurance Information', {
            'fields': ('insurance_provider', 'insurance_policy_number', 'insurance_group_number')
        }),
        ('FHIR Information', {
            'fields': ('identifier_system',)
        }),
    )

@admin.register(CommunityHealthProvider)
class CommunityHealthProviderAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'years_of_experience', 'service_area', 'is_active')
    list_filter = ('is_active', 'specialization', 'years_of_experience')
    search_fields = ('user__email', 'user__username', 'user__first_name', 'user__last_name', 
                    'specialization', 'service_area', 'certification_number')
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'is_active')
        }),
        ('Professional Details', {
            'fields': ('certification_number', 'years_of_experience', 'specialization')
        }),
        ('Service Information', {
            'fields': ('service_area', 'languages_spoken', 'availability_hours')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('username', 'activity', 'email_address', 'role', 'status', 'created_at')
    list_filter = ('activity', 'status', 'role', 'created_at')
    search_fields = ('username', 'email_address', 'activity', 'role')
    readonly_fields = ('id', 'created_at', 'updated_at', 'formatted_time_spent')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'username', 'activity', 'email_address', 'role', 'status')
        }),
        ('Timing Information', {
            'fields': ('time_spent', 'formatted_time_spent', 'date_joined', 'last_active')
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent', 'session_id', 'details'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Audit logs should not be manually created through admin
        return False
    
    def has_change_permission(self, request, obj=None):
        # Audit logs should not be modified
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete audit logs
        return request.user.is_superuser

