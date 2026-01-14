from rest_framework import serializers
from .models import (
    HealthCare, Appointment, Consultation, ConsultationChat, DoctorRating,
    Article, ArticleComment, ArticleCommentLike, Package, PatientDoctorAssignment, PatientSubscription, DoctorAvailability, Payment,
    PatientJournal, Referral,
    # AppointmentDocument, Resource,
)
from doctors.serializers import DoctorSerializer
from doctors.models import Doctor
from users.models import Patient, User

class HealthCareSerializer(serializers.ModelSerializer):
    doctors = DoctorSerializer(many=True, read_only=True)
    doctor_ids = serializers.ListField(
        child=serializers.UUIDField(), 
        write_only=True, 
        required=False,
        help_text="List of doctor IDs to associate with this facility"
    )
    part_of_name = serializers.SerializerMethodField(read_only=True, help_text="Name of parent organization")
    
    # Add explicit field definitions with help_text for Swagger documentation
    name = serializers.CharField(help_text="Name of the healthcare facility")
    description = serializers.CharField(help_text="Description of the healthcare facility")
    category = serializers.ChoiceField(
        choices=HealthCare._meta.get_field('category').choices,
        help_text="Category of healthcare facility (GENERAL, PEDIATRIC, MENTAL, DENTAL, VISION, OTHER)"
    )
    address = serializers.CharField(help_text="Main address of the healthcare facility")
    phone_number = serializers.CharField(help_text="Contact phone number")
    email = serializers.EmailField(help_text="Contact email address")
    website = serializers.URLField(required=False, help_text="Website URL")
    is_verified = serializers.BooleanField(required=False, help_text="Whether the facility is verified")
    is_active = serializers.BooleanField(required=False, help_text="Whether the facility is active")
    identifier_system = serializers.CharField(required=False, help_text="FHIR identifier system URI")
    part_of = serializers.PrimaryKeyRelatedField(
        queryset=HealthCare.objects.all(), 
        required=False, 
        allow_null=True,
        help_text="ID of parent organization (if applicable)"
    )
    city = serializers.CharField(required=False, help_text="City")
    state = serializers.CharField(required=False, help_text="State/Province")
    postal_code = serializers.CharField(required=False, help_text="Postal/ZIP code")
    country = serializers.CharField(required=False, help_text="Country")
    
    class Meta:
        model = HealthCare
        fields = [
            'id', 'name', 'description', 'category', 'address', 
            'phone_number', 'email', 'website', 'is_verified', 
            'is_active', 'doctors', 'doctor_ids', 
            'identifier_system', 'part_of', 'part_of_name',
            'city', 'state', 'postal_code', 'country',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_part_of_name(self, obj):
        if obj.part_of:
            return obj.part_of.name
        return None
    
    def create(self, validated_data):
        doctor_ids = validated_data.pop('doctor_ids', [])
        healthcare = HealthCare.objects.create(**validated_data)
        
        from doctors.models import Doctor
        for doctor_id in doctor_ids:
            try:
                doctor = Doctor.objects.get(id=doctor_id)
                healthcare.doctors.add(doctor)
            except Doctor.DoesNotExist:
                pass
        
        return healthcare
    
    def to_representation(self, instance):
        """
        If FHIR format is requested, return FHIR JSON representation.
        """
        request = self.context.get('request')
        
        # Default to standard representation
        if not request or not request.query_params.get('format') == 'fhir':
            return super().to_representation(instance)
        
        # Return FHIR format
        return instance.to_fhir_json()

class PatientDoctorAssignmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField(help_text="Patient's full name")
    doctor_name = serializers.SerializerMethodField(help_text="Doctor's full name")
    healthcare_facility_name = serializers.SerializerMethodField(read_only=True, help_text="Healthcare facility name")
    
    # Add explicit field definitions with help_text for Swagger documentation
    patient = serializers.PrimaryKeyRelatedField(
        queryset=Patient.objects.all(),
        help_text="ID of the patient"
    )
    doctor = serializers.PrimaryKeyRelatedField(
        queryset=Doctor.objects.all(),
        help_text="ID of the doctor"
    )
    notes = serializers.CharField(required=False, help_text="Assignment notes")
    is_active = serializers.BooleanField(required=False, help_text="Whether the assignment is active")
    status = serializers.ChoiceField(
        choices=PatientDoctorAssignment._meta.get_field('status').choices,
        required=False,
        help_text="FHIR Encounter status code"
    )
    encounter_type = serializers.ChoiceField(
        choices=PatientDoctorAssignment._meta.get_field('encounter_type').choices,
        required=False,
        help_text="FHIR Encounter type code"
    )
    identifier_system = serializers.CharField(required=False, help_text="FHIR identifier system URI")
    reason = serializers.CharField(required=False, help_text="Reason for the encounter")
    healthcare_facility = serializers.PrimaryKeyRelatedField(
        queryset=HealthCare.objects.all(),
        required=False,
        allow_null=True,
        help_text="ID of the healthcare facility where the encounter takes place"
    )
    scheduled_start = serializers.DateTimeField(required=False, allow_null=True, help_text="Scheduled start time")
    scheduled_end = serializers.DateTimeField(required=False, allow_null=True, help_text="Scheduled end time")
    actual_start = serializers.DateTimeField(required=False, allow_null=True, help_text="Actual start time")
    actual_end = serializers.DateTimeField(required=False, allow_null=True, help_text="Actual end time")
    
    class Meta:
        model = PatientDoctorAssignment
        fields = [
            'id', 'patient', 'doctor', 'patient_name', 'doctor_name', 
            'notes', 'is_active', 'status', 'encounter_type',
            'identifier_system', 'reason', 'healthcare_facility', 
            'healthcare_facility_name', 'scheduled_start', 'scheduled_end',
            'actual_start', 'actual_end', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    # No need for __init__ now that we import Patient at the top
    
    def get_patient_name(self, obj):
        return obj.patient.user.get_full_name() or obj.patient.user.username
    
    def get_doctor_name(self, obj):
        return obj.doctor.user.get_full_name() or obj.doctor.user.username
    
    def get_healthcare_facility_name(self, obj):
        if obj.healthcare_facility:
            return obj.healthcare_facility.name
        return "Not Specified"
    
    def to_representation(self, instance):
        """
        If FHIR format is requested, return FHIR JSON representation.
        """
        request = self.context.get('request')
        
        # Default to standard representation
        if not request or not request.query_params.get('format') == 'fhir':
            return super().to_representation(instance)
        
        # Return FHIR format
        return instance.to_fhir_json()


class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = DoctorAvailability
        fields = [
            'id', 'doctor', 'doctor_name', 'day_of_week', 'start_time', 'end_time',
            'is_recurring', 'specific_date', 'is_available', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def get_doctor_name(self, obj):
        return obj.doctor.user.get_full_name() or obj.doctor.user.username


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField(read_only=True)
    doctor_name = serializers.SerializerMethodField(read_only=True)
    healthcare_facility_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'doctor', 'patient_name', 'doctor_name',
            'appointment_date', 'start_time', 'end_time', 'status',
            'appointment_type', 'reason', 'diagnosis', 'treatment', 
            'notes', 'risk_level', 'identifier_system',
            'healthcare_facility', 'healthcare_facility_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def get_patient_name(self, obj):
        return obj.patient.user.get_full_name() or obj.patient.user.username
    
    def get_doctor_name(self, obj):
        return obj.doctor.user.get_full_name() or obj.doctor.user.username
    
    def get_healthcare_facility_name(self, obj):
        if obj.healthcare_facility:
            return obj.healthcare_facility.name
        return "Not Specified"
    
    def validate(self, attrs):
        """
        Validate appointment times to prevent overlapping bookings
        """
        from django.db.models import Q
        from datetime import datetime, timedelta
        
        doctor = attrs.get('doctor')
        patient = attrs.get('patient')
        appointment_date = attrs.get('appointment_date')
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        
        # Check if this is an update (instance exists)
        instance_id = getattr(self.instance, 'id', None) if self.instance else None
        
        if all([doctor, appointment_date, start_time, end_time]):
            # Convert times to datetime for comparison
            appointment_datetime = datetime.combine(appointment_date, start_time)
            appointment_end_datetime = datetime.combine(appointment_date, end_time)
            
            # Check for overlapping appointments for the same doctor
            doctor_conflicts = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                status__in=['scheduled', 'confirmed', 'in_progress']  # Active statuses
            )
            
            # Exclude current instance if updating
            if instance_id:
                doctor_conflicts = doctor_conflicts.exclude(id=instance_id)
            
            for existing_appointment in doctor_conflicts:
                existing_start = datetime.combine(
                    existing_appointment.appointment_date,
                    existing_appointment.start_time
                )
                existing_end = datetime.combine(
                    existing_appointment.appointment_date,
                    existing_appointment.end_time
                )
                
                # Check for time overlap
                if (appointment_datetime < existing_end and 
                    appointment_end_datetime > existing_start):
                    raise serializers.ValidationError(
                        f"Doctor is not available at this time. Conflicting appointment exists from "
                        f"{existing_appointment.start_time} to {existing_appointment.end_time}"
                    )
            
            # Check for overlapping appointments for the same patient
            patient_conflicts = Appointment.objects.filter(
                patient=patient,
                appointment_date=appointment_date,
                status__in=['scheduled', 'confirmed', 'in_progress']
            )
            
            # Exclude current instance if updating
            if instance_id:
                patient_conflicts = patient_conflicts.exclude(id=instance_id)
            
            for existing_appointment in patient_conflicts:
                existing_start = datetime.combine(
                    existing_appointment.appointment_date,
                    existing_appointment.start_time
                )
                existing_end = datetime.combine(
                    existing_appointment.appointment_date,
                    existing_appointment.end_time
                )
                
                # Check for time overlap
                if (appointment_datetime < existing_end and 
                    appointment_end_datetime > existing_start):
                    raise serializers.ValidationError(
                        f"Patient already has an appointment at this time from "
                        f"{existing_appointment.start_time} to {existing_appointment.end_time}"
                    )
            
            # Validate against doctor availability
            from healthcare.models import DoctorAvailability
            weekday = appointment_date.weekday()
            
            available_slots = DoctorAvailability.objects.filter(
                doctor=doctor,
                weekday=weekday,
                is_available=True
            )
            
            if not available_slots.exists():
                raise serializers.ValidationError(
                    f"Doctor is not available on {appointment_date.strftime('%A')}"
                )
            
            # Check if appointment time falls within available hours
            time_available = False
            for slot in available_slots:
                if slot.start_time <= start_time and slot.end_time >= end_time:
                    time_available = True
                    break
            
            if not time_available:
                available_times = ", ".join([
                    f"{slot.start_time} - {slot.end_time}" 
                    for slot in available_slots
                ])
                raise serializers.ValidationError(
                    f"Doctor is not available at this time. Available hours: {available_times}"
                )
        
        return attrs
    
    def to_representation(self, instance):
        """
        If FHIR format is requested, return FHIR JSON representation.
        """
        request = self.context.get('request')
        
        # Default to standard representation
        if not request or not request.query_params.get('format') == 'fhir':
            return super().to_representation(instance)
        
        # Return FHIR format
        return instance.to_fhir_json()


# class AppointmentDocumentSerializer(serializers.ModelSerializer):
#     uploaded_by_name = serializers.SerializerMethodField(read_only=True)
#     appointment_details = serializers.SerializerMethodField(read_only=True)
#     
#     class Meta:
#         model = AppointmentDocument
#         fields = [
#             'id', 'appointment', 'appointment_details', 'title', 'file',
#             'document_type', 'description', 'uploaded_by', 'uploaded_by_name',
#             'created_at', 'updated_at'
#         ]
#         read_only_fields = ['id', 'created_at', 'updated_at']
#         
#     def get_uploaded_by_name(self, obj):
#         if obj.uploaded_by:
#             return obj.uploaded_by.get_full_name() or obj.uploaded_by.username
#         return None
#     
#     def get_appointment_details(self, obj):
#         return {
#             'id': str(obj.appointment.id),
#             'patient': obj.appointment.patient.user.get_full_name(),
#             'doctor': obj.appointment.doctor.user.get_full_name(),
#             'date': obj.appointment.appointment_date,
#             'time': f"{obj.appointment.start_time} - {obj.appointment.end_time}"
#         }
# 
# 
class ConsultationChatSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField(read_only=True)
    sender_role = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = ConsultationChat
        fields = [
            'id', 'consultation', 'message', 'sender', 'sender_name', 'sender_role',
            'is_doctor', 'is_read', 'read_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_doctor', 'is_read', 'read_at', 'created_at', 'updated_at']
        
    def get_sender_name(self, obj):
        return obj.sender.get_full_name() or obj.sender.username
    
    def get_sender_role(self, obj):
        # Get user role based on roles many-to-many field
        roles = obj.sender.roles.all().values_list('name', flat=True)
        if 'doctor' in roles:
            return 'doctor'
        elif 'patient' in roles:
            return 'patient'
        elif 'admin' in roles:
            return 'admin'
        return 'user'
    
    def create(self, validated_data):
        # Set is_doctor flag based on user role
        sender = validated_data.get('sender')
        is_doctor = sender.roles.filter(name='doctor').exists()
        
        # Create message with proper is_doctor flag
        message = ConsultationChat.objects.create(
            **validated_data,
            is_doctor=is_doctor
        )
        return message


class ConsultationSerializer(serializers.ModelSerializer):
    appointment_details = serializers.SerializerMethodField(read_only=True)
    messages = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Consultation
        fields = [
            'id', 'appointment', 'appointment_details', 'status', 'start_time',
            'end_time', 'session_id', 'recording_url', 'twilio_room_name', 
            'messages', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'twilio_room_name', 
                           'twilio_room_sid', 'doctor_token', 'patient_token']
        
    def get_appointment_details(self, obj):
        healthcare_facility = obj.appointment.healthcare_facility
        return {
            'id': str(obj.appointment.id),
            'patient': obj.appointment.patient.user.get_full_name(),
            'doctor': obj.appointment.doctor.user.get_full_name(),
            'date': obj.appointment.appointment_date,
            'time': f"{obj.appointment.start_time} - {obj.appointment.end_time}",
            'institution_name': healthcare_facility.name if healthcare_facility else None,
            'institution_type': healthcare_facility.get_category_display() if healthcare_facility else None
        }
    
    def get_messages(self, obj):
        # Only include chat messages when explicitly requested
        if self.context.get('include_messages'):
            # Limit to most recent messages by default
            limit = self.context.get('messages_limit', 20)
            messages = obj.chat_messages.all().order_by('-created_at')[:limit]
            return ConsultationChatSerializer(messages, many=True).data
        return []


# class PackageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Package
#         fields = [
#             'id', 'name', 'description', 'price', 'duration_days',
#             'consultation_count', 'max_doctors', 'priority_support',
#             'access_to_resources', 'is_active', 'created_at', 'updated_at'
#         ]
#         read_only_fields = ['id', 'created_at', 'updated_at']
# 
# 
# class PatientSubscriptionSerializer(serializers.ModelSerializer):
#     patient_name = serializers.SerializerMethodField(read_only=True)
#     package_details = serializers.SerializerMethodField(read_only=True)
#     
#     class Meta:
#         model = PatientSubscription
#         fields = [
#             'id', 'patient', 'patient_name', 'package', 'package_details',
#             'start_date', 'end_date', 'status', 'consultations_used',
#             'payment_reference', 'payment_date', 'created_at', 'updated_at'
#         ]
#         read_only_fields = ['id', 'created_at', 'updated_at']
#         
#     def get_patient_name(self, obj):
#         return obj.patient.user.get_full_name() or obj.patient.user.username
#     
#     def get_package_details(self, obj):
#         return {
#             'id': str(obj.package.id),
#             'name': obj.package.name,
#             'price': str(obj.package.price),
#             'duration_days': obj.package.duration_days,
#             'consultation_count': obj.package.consultation_count
#         }
# 
# 
# class ResourceSerializer(serializers.ModelSerializer):
#     author_name = serializers.SerializerMethodField(read_only=True)
#     approved_by_name = serializers.SerializerMethodField(read_only=True)
#     
#     class Meta:
#         model = Resource
#         fields = [
#             'id', 'title', 'description', 'content_type', 'file', 'url',
#             'text_content', 'is_password_protected', 'password_hash',
#             'category', 'tags', 'author', 'author_name', 'is_approved',
#             'approved_by', 'approved_by_name', 'is_active',
#             'created_at', 'updated_at'
#         ]
#         read_only_fields = ['id', 'created_at', 'updated_at']
#         extra_kwargs = {
#             'password_hash': {'write_only': True}
#         }
#         
#     def get_author_name(self, obj):
#         if obj.author:
#             return obj.author.user.get_full_name() or obj.author.user.username
#         return None
#     
#     def get_approved_by_name(self, obj):
#         if obj.approved_by:
#             return obj.approved_by.get_full_name() or obj.approved_by.username
#         return None
# 
# 
class DoctorRatingSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField(read_only=True)
    doctor_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = DoctorRating
        fields = [
            'id', 'doctor', 'doctor_name', 'patient', 'patient_name',
            'rating', 'review', 'is_anonymous', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def get_patient_name(self, obj):
        if obj.is_anonymous:
            return "Anonymous"
        return obj.patient.user.get_full_name() or obj.patient.user.username
    
    def get_doctor_name(self, obj):
        return obj.doctor.user.get_full_name() or obj.doctor.user.username

# 
class ArticleCommentSerializer(serializers.ModelSerializer):
     user_name = serializers.SerializerMethodField(read_only=True)
     user_role = serializers.SerializerMethodField(read_only=True)
     replies = serializers.SerializerMethodField(read_only=True)
     
     class Meta:
         model = ArticleComment
         fields = [
             'id', 'article', 'content', 'user', 'user_name', 'user_role',
             'is_doctor', 'parent_comment', 'like_count', 'replies',
             'created_at', 'updated_at'
         ]
         read_only_fields = ['id', 'is_doctor', 'like_count', 'created_at', 'updated_at']
         
     def get_user_name(self, obj):
         return obj.user.get_full_name() or obj.user.username
     
     def get_user_role(self, obj):
         # Get user role based on roles many-to-many field
         roles = obj.user.roles.all().values_list('name', flat=True)
         if 'doctor' in roles:
             return 'doctor'
         elif 'patient' in roles:
             return 'patient'
         elif 'admin' in roles:
             return 'admin'
         return 'user'
     
     def get_replies(self, obj):
         # Don't recursively serialize replies for parent comments to avoid circular serialization
         if obj.parent_comment is None:  # Only for top-level comments
             replies = obj.replies.all()
             return ArticleCommentReplySerializer(replies, many=True).data
         return []
     
     def create(self, validated_data):
         # Set is_doctor flag based on user role
         user = validated_data.get('user')
         is_doctor = user.roles.filter(name='doctor').exists()
         
         # Create comment with proper is_doctor flag
         comment = ArticleComment.objects.create(
             **validated_data,
             is_doctor=is_doctor
         )
         return comment
 
 
class ArticleCommentReplySerializer(serializers.ModelSerializer):
     """
     Simplified serializer for comment replies to avoid circular nesting
     """
     user_name = serializers.SerializerMethodField(read_only=True)
     user_role = serializers.SerializerMethodField(read_only=True)
     
     class Meta:
         model = ArticleComment
         fields = [
             'id', 'content', 'user', 'user_name', 'user_role',
             'is_doctor', 'like_count', 'created_at', 'updated_at'
         ]
         read_only_fields = ['id', 'is_doctor', 'like_count', 'created_at', 'updated_at']
         
     def get_user_name(self, obj):
         return obj.user.get_full_name() or obj.user.username
     
     def get_user_role(self, obj):
         # Get user role based on roles many-to-many field
         roles = obj.user.roles.all().values_list('name', flat=True)
         if 'doctor' in roles:
             return 'doctor'
         elif 'patient' in roles:
             return 'patient'
         elif 'admin' in roles:
             return 'admin'
         return 'user'
 
 
class ArticleCommentLikeSerializer(serializers.ModelSerializer):
     user_name = serializers.SerializerMethodField(read_only=True)
     
     class Meta:
         model = ArticleCommentLike
         fields = ['id', 'comment', 'user', 'user_name', 'created_at']
         read_only_fields = ['id', 'created_at']
         
     def get_user_name(self, obj):
         return obj.user.get_full_name() or obj.user.username
# 
# 
class ArticleSerializer(serializers.ModelSerializer):
     author_name = serializers.SerializerMethodField(read_only=True)
     approved_by_name = serializers.SerializerMethodField(read_only=True)
     rejected_by_name = serializers.SerializerMethodField(read_only=True)
     comments_count = serializers.SerializerMethodField(read_only=True)
     category_display = serializers.SerializerMethodField(read_only=True)
     
     class Meta:
         model = Article
         fields = [
             'id', 'title', 'content', 'summary', 'author', 'author_name',
             'category', 'category_display', 'tags', 'featured_image', 'visibility',
             'is_featured', 'related_conditions', 'reading_time',
             'is_approved', 'approved_by', 'approved_by_name', 'approval_date', 'approval_notes',
             'is_rejected', 'rejected_by', 'rejected_by_name', 'rejection_date', 'rejection_reason',
             'is_published', 'publish_date', 'view_count', 'comments_count',
             'created_at', 'updated_at'
         ]
         read_only_fields = [
             'id', 'is_approved', 'approved_by', 'approval_date', 'approval_notes',
             'is_rejected', 'rejected_by', 'rejection_date', 'rejection_reason',
             'view_count', 'comments_count', 'created_at', 'updated_at'
         ]
         
     def get_author_name(self, obj):
         if obj.author:
             return obj.author.user.get_full_name() or obj.author.user.username
         return None
     
     def get_approved_by_name(self, obj):
         if obj.approved_by:
             return obj.approved_by.get_full_name() or obj.approved_by.username
         return None
     
     def get_rejected_by_name(self, obj):
         if obj.rejected_by:
             return obj.rejected_by.get_full_name() or obj.rejected_by.username
         return None
     
     def get_comments_count(self, obj):
         return obj.comments.count()  # This returns an integer that will be converted to a string in the JSON response
     
     def get_category_display(self, obj):
         return dict(obj._meta.get_field('category').choices).get(obj.category, obj.category)


class PackageSerializer(serializers.ModelSerializer):
    """
    Serializer for Package model
    """
    class Meta:
        model = Package
        fields = [
            'id', 'name', 'description', 'price', 'duration_days', 
            'consultation_limit', 'features', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for Payment model
    """
    class Meta:
        model = Payment
        fields = [
            'id', 'reference', 'amount', 'currency', 'payment_method', 
            'status', 'gateway_transaction_id', 'gateway_response',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'gateway_response']


class PatientSubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for PatientSubscription model
    """
    patient_name = serializers.SerializerMethodField(read_only=True)
    package_name = serializers.SerializerMethodField(read_only=True)
    package_details = PackageSerializer(source='package', read_only=True)
    payment_details = PaymentSerializer(source='payment', read_only=True)
    is_active = serializers.ReadOnlyField()
    consultations_remaining = serializers.ReadOnlyField()
    
    class Meta:
        model = PatientSubscription
        fields = [
            'id', 'patient', 'package', 'payment', 'patient_name', 'package_name', 
            'package_details', 'payment_details', 'status', 'start_date', 'end_date', 
            'consultations_used', 'is_active', 'consultations_remaining',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_patient_name(self, obj):
        return obj.patient.user.get_full_name() or obj.patient.user.username
    
    def get_package_name(self, obj):
        return obj.package.name


class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    """
    Serializer for DoctorAvailability model
    """
    doctor_name = serializers.SerializerMethodField(read_only=True)
    weekday_display = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = DoctorAvailability
        fields = [
            'id', 'doctor', 'doctor_name', 'weekday', 'weekday_display',
            'start_time', 'end_time', 'is_available',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_doctor_name(self, obj):
        return obj.doctor.user.get_full_name() or obj.doctor.user.username
    
    def get_weekday_display(self, obj):
        return obj.get_weekday_display()


class PatientJournalSerializer(serializers.ModelSerializer):
    """
    Serializer for PatientJournal model with custom id handling
    """
    patient_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = PatientJournal
        fields = [
            'id', 'patient', 'patient_name', 'title', 'content', 'preview',
            'tags', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'preview', 'created_at', 'updated_at']
    
    def get_patient_name(self, obj):
        return obj.patient.user.get_full_name() or obj.patient.user.username
    
    def to_representation(self, instance):
        """
        Custom representation to match the requested JSON structure
        """
        representation = super().to_representation(instance)
        return {
            'id': representation['id'],
            'title': representation['title'],
            'preview': representation['preview'],
            'created_at': representation['created_at'],
            'updated_at': representation['updated_at'],
            'tags': representation['tags']
        }


class RiskSegmentationSerializer(serializers.Serializer):
    """
    Serializer for risk segmentation dashboard data
    """
    risk_level = serializers.CharField(help_text="Risk level category (severe, high, moderate, low)")
    patient_count = serializers.IntegerField(help_text="Number of patients in this risk category")
    percentage = serializers.FloatField(help_text="Percentage of total patients")
    
    def to_representation(self, instance):
        return instance


class RiskSegmentationSummarySerializer(serializers.Serializer):
    """
    Serializer for risk segmentation summary statistics
    """
    total_patients = serializers.IntegerField(help_text="Total number of patients")
    distribution = RiskSegmentationSerializer(many=True, help_text="Risk level distribution")
    date_range = serializers.DictField(help_text="Applied date filter range", required=False)
    county_filter = serializers.CharField(help_text="Applied county filter", required=False, allow_blank=True)
    
    def to_representation(self, instance):
        return instance


class PatientRiskListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing patients by risk level
    """
    patient_name = serializers.SerializerMethodField(read_only=True)
    patient_email = serializers.SerializerMethodField(read_only=True)
    age = serializers.SerializerMethodField(read_only=True)
    county = serializers.SerializerMethodField(read_only=True)
    latest_appointment_date = serializers.SerializerMethodField(read_only=True)
    doctor_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'patient_name', 'patient_email', 'age', 'county', 
            'risk_level', 'appointment_date', 'latest_appointment_date',
            'doctor_name', 'diagnosis', 'treatment', 'notes'
        ]
    
    def get_patient_name(self, obj):
        return obj.patient.user.get_full_name() or obj.patient.user.username
    
    def get_patient_email(self, obj):
        return obj.patient.user.email
    
    def get_age(self, obj):
        if obj.patient.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - obj.patient.date_of_birth.year - ((today.month, today.day) < (obj.patient.date_of_birth.month, obj.patient.date_of_birth.day))
        return None
    
    def get_county(self, obj):
        # Extract county from patient's address or healthcare facility
        if obj.healthcare_facility and hasattr(obj.healthcare_facility, 'city'):
            return obj.healthcare_facility.city
        # Could also extract from patient.user.address if available
        return obj.patient.user.address.split(',')[0].strip() if obj.patient.user.address else None
    
    def get_latest_appointment_date(self, obj):
        return obj.appointment_date
    
    def get_doctor_name(self, obj):
        return obj.doctor.user.get_full_name() or obj.doctor.user.username


class ReferralCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating referrals by CHPs"""
    
    patient_id = serializers.UUIDField(help_text="ID of the patient to refer")
    doctor_id = serializers.UUIDField(help_text="ID of the doctor to refer to")
    
    class Meta:
        model = Referral
        fields = [
            'patient_id', 'doctor_id', 'referral_reason', 'clinical_notes', 
            'urgency', 'follow_up_required', 'follow_up_notes'
        ]
        
    def validate_patient_id(self, value):
        """Validate that patient exists"""
        try:
            patient = Patient.objects.get(id=value)
            return patient
        except Patient.DoesNotExist:
            raise serializers.ValidationError("Patient with this ID does not exist.")
    
    def validate_doctor_id(self, value):
        """Validate that doctor exists and accepts referrals"""
        try:
            doctor = Doctor.objects.get(id=value)
            if not doctor.accepts_referrals:
                raise serializers.ValidationError("This doctor does not accept referrals.")
            return doctor
        except Doctor.DoesNotExist:
            raise serializers.ValidationError("Doctor with this ID does not exist.")
    
    def create(self, validated_data):
        from users.models import CommunityHealthProvider

        patient = validated_data.pop('patient_id')
        doctor = validated_data.pop('doctor_id')

        # Get CHP from user
        try:
            chp = CommunityHealthProvider.objects.get(user=self.context['request'].user)
        except CommunityHealthProvider.DoesNotExist:
            raise serializers.ValidationError("User is not a Community Health Provider")

        referral = Referral.objects.create(
            patient=patient,
            referred_to_doctor=doctor,
            referring_chp=chp,
            **validated_data
        )
        return referral


class ReferralListSerializer(serializers.ModelSerializer):
    """Serializer for listing referrals with detailed information"""

    patient_id = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    patient_email = serializers.SerializerMethodField()
    patient_phone = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    doctor_specialty = serializers.SerializerMethodField()
    referring_chp_name = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    urgency_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Referral
        fields = [
            'id', 'patient_id', 'patient_name', 'patient_email', 'patient_phone',
            'doctor_name', 'doctor_specialty', 'referring_chp_name',
            'referral_reason', 'clinical_notes', 'urgency', 'urgency_display',
            'status', 'status_display', 'follow_up_required', 'follow_up_notes',
            'accepted_at', 'completed_at', 'doctor_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_patient_id(self, obj):
        return str(obj.patient.id)

    def get_patient_name(self, obj):
        return obj.patient.user.get_full_name() or obj.patient.user.username
    
    def get_patient_email(self, obj):
        return obj.patient.user.email
    
    def get_patient_phone(self, obj):
        return obj.patient.user.phone_number
    
    def get_doctor_name(self, obj):
        return f"Dr. {obj.referred_to_doctor.user.get_full_name()}"
    
    def get_doctor_specialty(self, obj):
        return obj.referred_to_doctor.specialty
    
    def get_referring_chp_name(self, obj):
        return obj.referring_chp.user.get_full_name()
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def get_urgency_display(self, obj):
        return obj.get_urgency_display()


class ReferralDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for individual referral view"""
    
    patient = serializers.SerializerMethodField()
    referred_to_doctor = serializers.SerializerMethodField()
    referring_chp = serializers.SerializerMethodField()
    
    class Meta:
        model = Referral
        fields = '__all__'
        read_only_fields = ['id', 'referring_chp', 'created_at', 'updated_at']
    
    def get_patient(self, obj):
        return {
            'id': obj.patient.id,
            'name': obj.patient.user.get_full_name() or obj.patient.user.username,
            'email': obj.patient.user.email,
            'phone': obj.patient.user.phone_number,
            'date_of_birth': obj.patient.date_of_birth,
            'gender': obj.patient.gender,
        }
    
    def get_referred_to_doctor(self, obj):
        return {
            'id': obj.referred_to_doctor.id,
            'name': f"Dr. {obj.referred_to_doctor.user.get_full_name()}",
            'specialty': obj.referred_to_doctor.specialty,
            'email': obj.referred_to_doctor.user.email,
            'facility': obj.referred_to_doctor.facility_name,
        }
    
    def get_referring_chp(self, obj):
        return {
            'id': obj.referring_chp.id,
            'name': obj.referring_chp.user.get_full_name(),
            'email': obj.referring_chp.user.email,
            'certification': obj.referring_chp.certification_number,
        }
