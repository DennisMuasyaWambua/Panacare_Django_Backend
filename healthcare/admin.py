from django.contrib import admin
from .models import HealthCare

@admin.register(HealthCare)
class HealthCareAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'address', 'phone_number', 'email', 'is_verified', 'is_active')
    list_filter = ('category', 'is_verified', 'is_active')
    search_fields = ('name', 'description', 'address', 'email')
    filter_horizontal = ('doctors',)

