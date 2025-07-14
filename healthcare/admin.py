from django.contrib import admin
from .models import Appointment, Consultation, HealthCare, Package, Payment

@admin.register(HealthCare)
class HealthCareAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'address', 'phone_number', 'email', 'is_verified', 'is_active')
    list_filter = ('category', 'is_verified', 'is_active')
    search_fields = ('name', 'description', 'address', 'email')
    # filter_horizontal = ('doctors',)  # Commented out as doctors field is not active


admin.site.register(Consultation)
admin.site.register(Appointment)
admin.site.register(Package)
admin.site.register(Payment)