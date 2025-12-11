from django.contrib import admin
from .models import Doctor

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialty', 'license_number', 'experience_years', 'is_verified', 'is_available')
    list_filter = ('specialty', 'is_verified', 'is_available')
    search_fields = ('user__email', 'user__username', 'user__first_name', 'user__last_name', 'specialty', 'license_number')

