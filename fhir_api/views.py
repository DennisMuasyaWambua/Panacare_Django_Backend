from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import Patient, Location as DjangoLocation
from doctors.models import Doctor
from healthcare.models import (
    HealthCare,
    Appointment as DjangoAppointment,
    PatientDoctorAssignment,
    Consultation,
    ConsultationChat,
    Referral,
    PatientSubscription,
    Payment
)

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Define the format parameter for Swagger documentation
format_parameter = openapi.Parameter(
    'format', 
    openapi.IN_QUERY, 
    description="Response format. Set to 'fhir' for FHIR-compliant responses", 
    type=openapi.TYPE_STRING,
    required=False,
    enum=['fhir']
)

from .adapters import (
    create_fhir_patient,
    create_fhir_practitioner,
    create_fhir_organization,
    create_fhir_appointment,
    create_fhir_encounter,
    create_fhir_service_request,
    create_fhir_document_reference,
    create_fhir_care_plan,
    create_fhir_care_team,
    create_fhir_task,
    create_fhir_communication,
    create_fhir_coverage,
    create_fhir_claim,
    create_fhir_consent,
    create_fhir_provenance,
    create_fhir_location
)
from .serializers import (
    PatientFHIRSerializer,
    PractitionerFHIRSerializer,
    OrganizationFHIRSerializer,
    EncounterFHIRSerializer,
    AppointmentFHIRSerializer,
    DocumentReferenceFHIRSerializer,
    DiagnosticReportFHIRSerializer,
    ProcedureFHIRSerializer,
    CarePlanFHIRSerializer,
    CareTeamFHIRSerializer,
    TaskFHIRSerializer,
    CommunicationFHIRSerializer,
    MedicationFHIRSerializer,
    CoverageFHIRSerializer,
    ClaimFHIRSerializer,
    ConsentFHIRSerializer,
    ProvenanceFHIRSerializer,
    ImmunizationFHIRSerializer,
    FamilyMemberHistoryFHIRSerializer,
    QuestionnaireResponseFHIRSerializer,
    SpecimenFHIRSerializer,
    LocationFHIRSerializer,
    DeviceFHIRSerializer,
    ServiceRequestFHIRSerializer,
    BundleSerializer,
    create_bundle
)


class FHIRPatientViewSet(viewsets.ViewSet):
    """
    ViewSet for FHIR Patient resources
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Return a list of all patients as FHIR Patient resources",
        responses={200: PatientFHIRSerializer(many=True)}
    )
    def list(self, request):
        """
        Return a list of all patients as FHIR Patient resources
        """
        patients = Patient.objects.all()
        
        # Convert each Patient to a FHIR Patient
        fhir_patients = [create_fhir_patient(patient) for patient in patients]
        
        # Create a Bundle containing all patients
        bundle = create_bundle(fhir_patients)
        
        # Serialize the bundle
        serializer = BundleSerializer(bundle)
        
        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"
        
        return response
    
    @swagger_auto_schema(
        operation_description="Return a single patient as a FHIR Patient resource",
        responses={200: PatientFHIRSerializer()}
    )
    def retrieve(self, request, pk=None):
        """
        Return a single patient as a FHIR Patient resource
        """
        patient = get_object_or_404(Patient, pk=pk)
        
        # Convert Patient to FHIR Patient
        fhir_patient = create_fhir_patient(patient)
        
        # Serialize the FHIR Patient
        serializer = PatientFHIRSerializer(fhir_patient)
        
        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"
        
        return response


class FHIRPractitionerViewSet(viewsets.ViewSet):
    """
    ViewSet for FHIR Practitioner resources
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Return a list of all doctors as FHIR Practitioner resources",
        responses={200: PractitionerFHIRSerializer(many=True)}
    )
    def list(self, request):
        """
        Return a list of all doctors as FHIR Practitioner resources
        """
        doctors = Doctor.objects.all()
        
        # Convert each Doctor to a FHIR Practitioner
        fhir_practitioners = [create_fhir_practitioner(doctor) for doctor in doctors]
        
        # Create a Bundle containing all practitioners
        bundle = create_bundle(fhir_practitioners)
        
        # Serialize the bundle
        serializer = BundleSerializer(bundle)
        
        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"
        
        return response
    
    @swagger_auto_schema(
        operation_description="Return a single doctor as a FHIR Practitioner resource",
        responses={200: PractitionerFHIRSerializer()}
    )
    def retrieve(self, request, pk=None):
        """
        Return a single doctor as a FHIR Practitioner resource
        """
        doctor = get_object_or_404(Doctor, pk=pk)
        
        # Convert Doctor to FHIR Practitioner
        fhir_practitioner = create_fhir_practitioner(doctor)
        
        # Serialize the FHIR Practitioner
        serializer = PractitionerFHIRSerializer(fhir_practitioner)
        
        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"
        
        return response


class FHIROrganizationViewSet(viewsets.ViewSet):
    """
    ViewSet for FHIR Organization resources
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Return a list of all healthcare facilities as FHIR Organization resources",
        responses={200: OrganizationFHIRSerializer(many=True)}
    )
    def list(self, request):
        """
        Return a list of all healthcare facilities as FHIR Organization resources
        """
        facilities = HealthCare.objects.all()
        
        # Convert each HealthCare to a FHIR Organization
        fhir_organizations = [create_fhir_organization(facility) for facility in facilities]
        
        # Create a Bundle containing all organizations
        bundle = create_bundle(fhir_organizations)
        
        # Serialize the bundle
        serializer = BundleSerializer(bundle)
        
        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"
        
        return response
    
    @swagger_auto_schema(
        operation_description="Return a single healthcare facility as a FHIR Organization resource",
        responses={200: OrganizationFHIRSerializer()}
    )
    def retrieve(self, request, pk=None):
        """
        Return a single healthcare facility as a FHIR Organization resource
        """
        facility = get_object_or_404(HealthCare, pk=pk)
        
        # Convert HealthCare to FHIR Organization
        fhir_organization = create_fhir_organization(facility)
        
        # Serialize the FHIR Organization
        serializer = OrganizationFHIRSerializer(fhir_organization)
        
        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"
        
        return response


class FHIRAppointmentViewSet(viewsets.ViewSet):
    """
    ViewSet for FHIR Appointment resources
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Return a list of all appointments as FHIR Appointment resources",
        responses={200: AppointmentFHIRSerializer(many=True)}
    )
    def list(self, request):
        """
        Return a list of all appointments as FHIR Appointment resources
        """
        appointments = DjangoAppointment.objects.all()

        # Convert each Appointment to a FHIR Appointment
        fhir_appointments = [create_fhir_appointment(appointment) for appointment in appointments]

        # Create a Bundle containing all appointments
        bundle = create_bundle(fhir_appointments)

        # Serialize the bundle
        serializer = BundleSerializer(bundle)

        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response

    @swagger_auto_schema(
        operation_description="Return a single appointment as a FHIR Appointment resource",
        responses={200: AppointmentFHIRSerializer()}
    )
    def retrieve(self, request, pk=None):
        """
        Return a single appointment as a FHIR Appointment resource
        """
        appointment = get_object_or_404(DjangoAppointment, pk=pk)

        # Convert Appointment to FHIR Appointment
        fhir_appointment = create_fhir_appointment(appointment)

        # Serialize the FHIR Appointment
        serializer = AppointmentFHIRSerializer(fhir_appointment)

        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response


class FHIREncounterViewSet(viewsets.ViewSet):
    """
    ViewSet for FHIR Encounter resources
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Return a list of all patient-doctor assignments as FHIR Encounter resources",
        responses={200: EncounterFHIRSerializer(many=True)}
    )
    def list(self, request):
        """
        Return a list of all patient-doctor assignments as FHIR Encounter resources
        """
        assignments = PatientDoctorAssignment.objects.all()

        # Convert each PatientDoctorAssignment to a FHIR Encounter
        fhir_encounters = [create_fhir_encounter(assignment) for assignment in assignments]

        # Create a Bundle containing all encounters
        bundle = create_bundle(fhir_encounters)

        # Serialize the bundle
        serializer = BundleSerializer(bundle)

        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response

    @swagger_auto_schema(
        operation_description="Return a single patient-doctor assignment as a FHIR Encounter resource",
        responses={200: EncounterFHIRSerializer()}
    )
    def retrieve(self, request, pk=None):
        """
        Return a single patient-doctor assignment as a FHIR Encounter resource
        """
        assignment = get_object_or_404(PatientDoctorAssignment, pk=pk)

        # Convert PatientDoctorAssignment to FHIR Encounter
        fhir_encounter = create_fhir_encounter(assignment)

        # Serialize the FHIR Encounter
        serializer = EncounterFHIRSerializer(fhir_encounter)

        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response


class FHIRServiceRequestViewSet(viewsets.ViewSet):
    """
    ViewSet for FHIR ServiceRequest resources (Referrals)
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Return a list of all referrals as FHIR ServiceRequest resources",
        responses={200: ServiceRequestFHIRSerializer(many=True)}
    )
    def list(self, request):
        """
        Return a list of all referrals as FHIR ServiceRequest resources
        """
        referrals = Referral.objects.all()

        # Convert each Referral to a FHIR ServiceRequest
        fhir_service_requests = [create_fhir_service_request(referral) for referral in referrals]

        # Create a Bundle containing all service requests
        bundle = create_bundle(fhir_service_requests)

        # Serialize the bundle
        serializer = BundleSerializer(bundle)

        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response

    @swagger_auto_schema(
        operation_description="Return a single referral as a FHIR ServiceRequest resource",
        responses={200: ServiceRequestFHIRSerializer()}
    )
    def retrieve(self, request, pk=None):
        """
        Return a single referral as a FHIR ServiceRequest resource
        """
        referral = get_object_or_404(Referral, pk=pk)

        # Convert Referral to FHIR ServiceRequest
        fhir_service_request = create_fhir_service_request(referral)

        # Serialize the FHIR ServiceRequest
        serializer = ServiceRequestFHIRSerializer(fhir_service_request)

        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response


class FHIRDocumentReferenceViewSet(viewsets.ViewSet):
    """
    ViewSet for FHIR DocumentReference resources (Consultation Documents)
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Return a list of all consultation documents as FHIR DocumentReference resources",
        responses={200: DocumentReferenceFHIRSerializer(many=True)}
    )
    def list(self, request):
        """
        Return a list of all consultation documents as FHIR DocumentReference resources
        """
        consultations = Consultation.objects.all()

        # Convert each Consultation to a FHIR DocumentReference
        fhir_doc_refs = [create_fhir_document_reference(consultation) for consultation in consultations]

        # Create a Bundle containing all document references
        bundle = create_bundle(fhir_doc_refs)

        # Serialize the bundle
        serializer = BundleSerializer(bundle)

        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response

    @swagger_auto_schema(
        operation_description="Return a single consultation document as a FHIR DocumentReference resource",
        responses={200: DocumentReferenceFHIRSerializer()}
    )
    def retrieve(self, request, pk=None):
        """
        Return a single consultation document as a FHIR DocumentReference resource
        """
        consultation = get_object_or_404(Consultation, pk=pk)

        # Convert Consultation to FHIR DocumentReference
        fhir_doc_ref = create_fhir_document_reference(consultation)

        # Serialize the FHIR DocumentReference
        serializer = DocumentReferenceFHIRSerializer(fhir_doc_ref)

        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response


class FHIRCarePlanViewSet(viewsets.ViewSet):
    """
    ViewSet for FHIR CarePlan resources
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Return a list of all care plans as FHIR CarePlan resources",
        responses={200: CarePlanFHIRSerializer(many=True)}
    )
    def list(self, request):
        """
        Return a list of all care plans as FHIR CarePlan resources
        """
        appointments = DjangoAppointment.objects.filter(treatment__isnull=False).exclude(treatment='')

        # Convert each Appointment to a FHIR CarePlan
        fhir_care_plans = [create_fhir_care_plan(appointment) for appointment in appointments]

        # Create a Bundle containing all care plans
        bundle = create_bundle(fhir_care_plans)

        # Serialize the bundle
        serializer = BundleSerializer(bundle)

        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response

    @swagger_auto_schema(
        operation_description="Return a single care plan as a FHIR CarePlan resource",
        responses={200: CarePlanFHIRSerializer()}
    )
    def retrieve(self, request, pk=None):
        """
        Return a single care plan as a FHIR CarePlan resource
        """
        appointment = get_object_or_404(DjangoAppointment, pk=pk)

        # Convert Appointment to FHIR CarePlan
        fhir_care_plan = create_fhir_care_plan(appointment)

        # Serialize the FHIR CarePlan
        serializer = CarePlanFHIRSerializer(fhir_care_plan)

        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response


class FHIRCareTeamViewSet(viewsets.ViewSet):
    """
    ViewSet for FHIR CareTeam resources
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Return a list of all care teams as FHIR CareTeam resources",
        responses={200: CareTeamFHIRSerializer(many=True)}
    )
    def list(self, request):
        """
        Return a list of all care teams as FHIR CareTeam resources
        """
        appointments = DjangoAppointment.objects.filter(created_by_chp__isnull=False)

        # Convert each Appointment to a FHIR CareTeam
        fhir_care_teams = [create_fhir_care_team(appointment) for appointment in appointments]

        # Create a Bundle containing all care teams
        bundle = create_bundle(fhir_care_teams)

        # Serialize the bundle
        serializer = BundleSerializer(bundle)

        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response

    @swagger_auto_schema(
        operation_description="Return a single care team as a FHIR CareTeam resource",
        responses={200: CareTeamFHIRSerializer()}
    )
    def retrieve(self, request, pk=None):
        """
        Return a single care team as a FHIR CareTeam resource
        """
        appointment = get_object_or_404(DjangoAppointment, pk=pk)

        # Convert Appointment to FHIR CareTeam
        fhir_care_team = create_fhir_care_team(appointment)

        # Serialize the FHIR CareTeam
        serializer = CareTeamFHIRSerializer(fhir_care_team)

        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response


class FHIRTaskViewSet(viewsets.ViewSet):
    """
    ViewSet for FHIR Task resources
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Return a list of all tasks as FHIR Task resources",
        responses={200: TaskFHIRSerializer(many=True)}
    )
    def list(self, request):
        """
        Return a list of all tasks as FHIR Task resources
        """
        referrals = Referral.objects.all()

        # Convert each Referral to a FHIR Task
        fhir_tasks = [create_fhir_task(referral) for referral in referrals]

        # Create a Bundle containing all tasks
        bundle = create_bundle(fhir_tasks)

        # Serialize the bundle
        serializer = BundleSerializer(bundle)

        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response

    @swagger_auto_schema(
        operation_description="Return a single task as a FHIR Task resource",
        responses={200: TaskFHIRSerializer()}
    )
    def retrieve(self, request, pk=None):
        """
        Return a single task as a FHIR Task resource
        """
        referral = get_object_or_404(Referral, pk=pk)

        # Convert Referral to FHIR Task
        fhir_task = create_fhir_task(referral)

        # Serialize the FHIR Task
        serializer = TaskFHIRSerializer(fhir_task)

        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response


class FHIRCommunicationViewSet(viewsets.ViewSet):
    """
    ViewSet for FHIR Communication resources
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Return a list of all communications as FHIR Communication resources",
        responses={200: CommunicationFHIRSerializer(many=True)}
    )
    def list(self, request):
        """
        Return a list of all communications as FHIR Communication resources
        """
        messages = ConsultationChat.objects.all()

        # Convert each ConsultationChat to a FHIR Communication
        fhir_communications = [create_fhir_communication(message) for message in messages]

        # Create a Bundle containing all communications
        bundle = create_bundle(fhir_communications)

        # Serialize the bundle
        serializer = BundleSerializer(bundle)

        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response

    @swagger_auto_schema(
        operation_description="Return a single communication as a FHIR Communication resource",
        responses={200: CommunicationFHIRSerializer()}
    )
    def retrieve(self, request, pk=None):
        """
        Return a single communication as a FHIR Communication resource
        """
        message = get_object_or_404(ConsultationChat, pk=pk)

        # Convert ConsultationChat to FHIR Communication
        fhir_communication = create_fhir_communication(message)

        # Serialize the FHIR Communication
        serializer = CommunicationFHIRSerializer(fhir_communication)

        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response


class FHIRCoverageViewSet(viewsets.ViewSet):
    """
    ViewSet for FHIR Coverage resources
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Return a list of all coverages as FHIR Coverage resources",
        responses={200: CoverageFHIRSerializer(many=True)}
    )
    def list(self, request):
        """
        Return a list of all coverages as FHIR Coverage resources
        """
        subscriptions = PatientSubscription.objects.all()

        # Convert each PatientSubscription to a FHIR Coverage
        fhir_coverages = [create_fhir_coverage(subscription) for subscription in subscriptions]

        # Create a Bundle containing all coverages
        bundle = create_bundle(fhir_coverages)

        # Serialize the bundle
        serializer = BundleSerializer(bundle)

        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response

    @swagger_auto_schema(
        operation_description="Return a single coverage as a FHIR Coverage resource",
        responses={200: CoverageFHIRSerializer()}
    )
    def retrieve(self, request, pk=None):
        """
        Return a single coverage as a FHIR Coverage resource
        """
        subscription = get_object_or_404(PatientSubscription, pk=pk)

        # Convert PatientSubscription to FHIR Coverage
        fhir_coverage = create_fhir_coverage(subscription)

        # Serialize the FHIR Coverage
        serializer = CoverageFHIRSerializer(fhir_coverage)

        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response


class FHIRClaimViewSet(viewsets.ViewSet):
    """
    ViewSet for FHIR Claim resources
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Return a list of all claims as FHIR Claim resources",
        responses={200: ClaimFHIRSerializer(many=True)}
    )
    def list(self, request):
        """
        Return a list of all claims as FHIR Claim resources
        """
        payments = Payment.objects.filter(subscriptions__isnull=False).distinct()

        # Convert each Payment to a FHIR Claim
        fhir_claims = []
        for payment in payments:
            subscription = payment.subscriptions.first()
            if subscription:
                fhir_claims.append(create_fhir_claim(payment, subscription))

        # Create a Bundle containing all claims
        bundle = create_bundle(fhir_claims)

        # Serialize the bundle
        serializer = BundleSerializer(bundle)

        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response

    @swagger_auto_schema(
        operation_description="Return a single claim as a FHIR Claim resource",
        responses={200: ClaimFHIRSerializer()}
    )
    def retrieve(self, request, pk=None):
        """
        Return a single claim as a FHIR Claim resource
        """
        payment = get_object_or_404(Payment, pk=pk)
        subscription = payment.subscriptions.first()

        if not subscription:
            return Response(
                {"error": "No subscription found for this payment"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Convert Payment to FHIR Claim
        fhir_claim = create_fhir_claim(payment, subscription)

        # Serialize the FHIR Claim
        serializer = ClaimFHIRSerializer(fhir_claim)

        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response


class FHIRConsentViewSet(viewsets.ViewSet):
    """
    ViewSet for FHIR Consent resources
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Return a list of all consents as FHIR Consent resources",
        responses={200: ConsentFHIRSerializer(many=True)}
    )
    def list(self, request):
        """
        Return a list of all consents as FHIR Consent resources
        """
        patients = Patient.objects.all()

        # Convert each Patient to a FHIR Consent
        fhir_consents = [create_fhir_consent(patient) for patient in patients]

        # Create a Bundle containing all consents
        bundle = create_bundle(fhir_consents)

        # Serialize the bundle
        serializer = BundleSerializer(bundle)

        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response

    @swagger_auto_schema(
        operation_description="Return a single consent as a FHIR Consent resource",
        responses={200: ConsentFHIRSerializer()}
    )
    def retrieve(self, request, pk=None):
        """
        Return a single consent as a FHIR Consent resource
        """
        patient = get_object_or_404(Patient, pk=pk)

        # Convert Patient to FHIR Consent
        fhir_consent = create_fhir_consent(patient)

        # Serialize the FHIR Consent
        serializer = ConsentFHIRSerializer(fhir_consent)

        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response


class FHIRLocationViewSet(viewsets.ViewSet):
    """
    ViewSet for FHIR Location resources
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Return a list of all locations as FHIR Location resources",
        responses={200: LocationFHIRSerializer(many=True)}
    )
    def list(self, request):
        """
        Return a list of all locations as FHIR Location resources
        """
        locations = DjangoLocation.objects.all()

        # Convert each Location to a FHIR Location
        fhir_locations = [create_fhir_location(location) for location in locations]

        # Create a Bundle containing all locations
        bundle = create_bundle(fhir_locations)

        # Serialize the bundle
        serializer = BundleSerializer(bundle)

        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response

    @swagger_auto_schema(
        operation_description="Return a single location as a FHIR Location resource",
        responses={200: LocationFHIRSerializer()}
    )
    def retrieve(self, request, pk=None):
        """
        Return a single location as a FHIR Location resource
        """
        location = get_object_or_404(DjangoLocation, pk=pk)

        # Convert Location to FHIR Location
        fhir_location = create_fhir_location(location)

        # Serialize the FHIR Location
        serializer = LocationFHIRSerializer(fhir_location)

        # Set appropriate content type for FHIR responses
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response


# FHIR metadata endpoint
@swagger_auto_schema(
    method='get',
    operation_description="Return FHIR server capability statement",
    responses={200: "FHIR CapabilityStatement"}
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def fhir_metadata(request):
    """
    Return FHIR server capability statement
    """
    metadata = {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": "2025-05-15",
        "publisher": "Panacare Healthcare",
        "kind": "instance",
        "software": {
            "name": "Panacare FHIR API",
            "version": "1.0.0"
        },
        "implementation": {
            "description": "Panacare Healthcare FHIR API",
            "url": request.build_absolute_uri('/fhir/')
        },
        "fhirVersion": "4.0.1",
        "format": ["json"],
        "rest": [
            {
                "mode": "server",
                "resource": [
                    {
                        "type": "Patient",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"}
                        ],
                        "searchParam": [
                            {"name": "_id", "type": "token"}
                        ]
                    },
                    {
                        "type": "Practitioner",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"}
                        ],
                        "searchParam": [
                            {"name": "_id", "type": "token"}
                        ]
                    },
                    {
                        "type": "Organization",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"}
                        ],
                        "searchParam": [
                            {"name": "_id", "type": "token"}
                        ]
                    },
                    {
                        "type": "Appointment",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"}
                        ],
                        "searchParam": [
                            {"name": "_id", "type": "token"},
                            {"name": "patient", "type": "reference"},
                            {"name": "practitioner", "type": "reference"},
                            {"name": "status", "type": "token"},
                            {"name": "date", "type": "date"}
                        ]
                    },
                    {
                        "type": "Encounter",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"}
                        ],
                        "searchParam": [
                            {"name": "_id", "type": "token"},
                            {"name": "patient", "type": "reference"},
                            {"name": "practitioner", "type": "reference"},
                            {"name": "status", "type": "token"}
                        ]
                    },
                    {
                        "type": "ServiceRequest",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"}
                        ],
                        "searchParam": [
                            {"name": "_id", "type": "token"},
                            {"name": "patient", "type": "reference"},
                            {"name": "requester", "type": "reference"},
                            {"name": "performer", "type": "reference"},
                            {"name": "status", "type": "token"}
                        ]
                    },
                    {
                        "type": "DocumentReference",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"}
                        ],
                        "searchParam": [
                            {"name": "_id", "type": "token"},
                            {"name": "patient", "type": "reference"},
                            {"name": "author", "type": "reference"},
                            {"name": "status", "type": "token"},
                            {"name": "date", "type": "date"}
                        ]
                    },
                    {
                        "type": "CarePlan",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"}
                        ],
                        "searchParam": [
                            {"name": "_id", "type": "token"},
                            {"name": "patient", "type": "reference"},
                            {"name": "status", "type": "token"}
                        ]
                    },
                    {
                        "type": "CareTeam",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"}
                        ],
                        "searchParam": [
                            {"name": "_id", "type": "token"},
                            {"name": "patient", "type": "reference"},
                            {"name": "status", "type": "token"}
                        ]
                    },
                    {
                        "type": "Task",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"}
                        ],
                        "searchParam": [
                            {"name": "_id", "type": "token"},
                            {"name": "patient", "type": "reference"},
                            {"name": "owner", "type": "reference"},
                            {"name": "requester", "type": "reference"},
                            {"name": "status", "type": "token"}
                        ]
                    },
                    {
                        "type": "Communication",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"}
                        ],
                        "searchParam": [
                            {"name": "_id", "type": "token"},
                            {"name": "patient", "type": "reference"},
                            {"name": "sender", "type": "reference"},
                            {"name": "recipient", "type": "reference"}
                        ]
                    },
                    {
                        "type": "Coverage",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"}
                        ],
                        "searchParam": [
                            {"name": "_id", "type": "token"},
                            {"name": "patient", "type": "reference"},
                            {"name": "beneficiary", "type": "reference"},
                            {"name": "status", "type": "token"}
                        ]
                    },
                    {
                        "type": "Claim",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"}
                        ],
                        "searchParam": [
                            {"name": "_id", "type": "token"},
                            {"name": "patient", "type": "reference"},
                            {"name": "status", "type": "token"}
                        ]
                    },
                    {
                        "type": "Consent",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"}
                        ],
                        "searchParam": [
                            {"name": "_id", "type": "token"},
                            {"name": "patient", "type": "reference"},
                            {"name": "status", "type": "token"}
                        ]
                    },
                    {
                        "type": "Location",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"}
                        ],
                        "searchParam": [
                            {"name": "_id", "type": "token"},
                            {"name": "name", "type": "string"},
                            {"name": "status", "type": "token"}
                        ]
                    }
                ]
            }
        ]
    }
    
    # Set appropriate content type for FHIR responses
    response = Response(metadata)
    response["Content-Type"] = "application/fhir+json"
    
    return response
