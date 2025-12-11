from django.contrib import admin
from .models import ClinicalDecisionRecord

@admin.register(ClinicalDecisionRecord)
class ClinicalDecisionRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'created_at', 'age', 'gender', 'risk_level')
    list_filter = ('gender', 'risk_level', 'high_blood_pressure', 'diabetes', 'on_medication')
    search_fields = ('patient__user__email', 'patient__user__first_name', 'patient__user__last_name')
    readonly_fields = ('id', 'created_at')
    fieldsets = (
        ('Patient Information', {
            'fields': ('id', 'patient', 'created_at', 'age', 'gender', 'weight', 'height')
        }),
        ('Medical History', {
            'fields': ('high_blood_pressure', 'diabetes', 'on_medication')
        }),
        ('Symptoms', {
            'fields': ('headache', 'dizziness', 'blurred_vision', 'palpitations', 'fatigue', 
                      'chest_pain', 'frequent_thirst', 'loss_of_appetite', 'frequent_urination',
                      'other_symptoms', 'no_symptoms')
        }),
        ('Vitals', {
            'fields': ('systolic_pressure', 'diastolic_pressure', 'blood_sugar', 'heart_rate')
        }),
        ('Lifestyle', {
            'fields': ('sleep_hours', 'exercise_minutes', 'eats_unhealthy', 'smokes', 
                      'consumes_alcohol', 'skips_medication')
        }),
        ('Analysis and Recommendations', {
            'fields': ('analysis', 'recommendations', 'risk_level')
        }),
    )
