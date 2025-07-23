from rest_framework import serializers
from .models import (
    HealthCare, Appointment, Consultation, ConsultationChat, DoctorRating,
    Article, ArticleComment, ArticleCommentLike, Package, PatientDoctorAssignment, PatientSubscription, DoctorAvailability, Payment,
    PatientDoctorAssignment,
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
        return None
    
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
        return None
    
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
        return {
            'id': str(obj.appointment.id),
            'patient': obj.appointment.patient.user.get_full_name(),
            'doctor': obj.appointment.doctor.user.get_full_name(),
            'date': obj.appointment.appointment_date,
            'time': f"{obj.appointment.start_time} - {obj.appointment.end_time}"
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
     comments_count = serializers.SerializerMethodField(read_only=True)
     category_display = serializers.SerializerMethodField(read_only=True)
     
     class Meta:
         model = Article
         fields = [
             'id', 'title', 'content', 'summary', 'author', 'author_name',
             'category', 'category_display', 'tags', 'featured_image', 'visibility',
             'is_featured', 'related_conditions', 'reading_time',
             'is_approved', 'approved_by', 'approved_by_name', 'approval_date', 'approval_notes',
             'is_published', 'publish_date', 'view_count', 'comments_count',
             'created_at', 'updated_at'
         ]
         read_only_fields = [
             'id', 'is_approved', 'approved_by', 'approval_date', 'approval_notes',
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
