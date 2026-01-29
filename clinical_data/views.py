"""
FHIR ViewSets for clinical data resources

These ViewSets provide read-only FHIR endpoints for clinical observations,
conditions, medication requests, medication statements, and allergies.
All endpoints return FHIR-compliant JSON with proper Content-Type headers.
"""

from rest_framework import viewsets, permissions
from rest_framework.response import Response
from django.shortcuts.get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import (
    ClinicalObservation,
    ClinicalCondition,
    ClinicalMedicationRequest,
    ClinicalMedicationStatement,
    ClinicalAllergyIntolerance,
)
from .adapters import (
    create_fhir_observation,
    create_fhir_condition,
    create_fhir_medication_request,
    create_fhir_medication_statement,
    create_fhir_allergy_intolerance,
)
from .serializers import (
    ObservationFHIRSerializer,
    ConditionFHIRSerializer,
    MedicationRequestFHIRSerializer,
    MedicationStatementFHIRSerializer,
    AllergyIntoleranceFHIRSerializer,
    BundleSerializer,
    create_bundle,
)


class FHIRObservationViewSet(viewsets.ViewSet):
    """
    FHIR Observation endpoint for clinical observations (vitals and symptoms).

    list: Return all observations as FHIR Bundle (searchset type)
    retrieve: Return single observation as FHIR Observation resource
    """

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve all clinical observations as FHIR Bundle. "
                              "Supports filtering by patient, category, code, and date.",
        manual_parameters=[
            openapi.Parameter(
                'patient',
                openapi.IN_QUERY,
                description="Filter by patient UUID",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'category',
                openapi.IN_QUERY,
                description="Filter by category (vital-signs, laboratory, exam, etc.)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'code',
                openapi.IN_QUERY,
                description="Filter by observation code (CIEL code)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'date',
                openapi.IN_QUERY,
                description="Filter by date (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format='date'
            ),
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Filter by status (final, preliminary, etc.)",
                type=openapi.TYPE_STRING
            ),
        ],
        responses={
            200: BundleSerializer,
            401: "Unauthorized"
        }
    )
    def list(self, request):
        """Return all observations as FHIR Bundle"""

        # Start with all observations
        observations = ClinicalObservation.objects.select_related(
            'patient', 'patient__user', 'encounter', 'performer'
        ).all()

        # Apply filters from query parameters
        patient_id = request.query_params.get('patient')
        if patient_id:
            observations = observations.filter(patient__id=patient_id)

        category = request.query_params.get('category')
        if category:
            observations = observations.filter(category=category)

        code = request.query_params.get('code')
        if code:
            observations = observations.filter(code=code)

        date = request.query_params.get('date')
        if date:
            observations = observations.filter(effective_datetime__date=date)

        status = request.query_params.get('status')
        if status:
            observations = observations.filter(status=status)

        # Convert to FHIR resources
        fhir_observations = [
            create_fhir_observation(obs) for obs in observations
        ]

        # Create bundle
        bundle = create_bundle(fhir_observations, bundle_type="searchset")

        # Serialize
        serializer = BundleSerializer(bundle)
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response

    @swagger_auto_schema(
        operation_description="Retrieve a single clinical observation as FHIR Observation resource",
        responses={
            200: ObservationFHIRSerializer,
            404: "Observation not found",
            401: "Unauthorized"
        }
    )
    def retrieve(self, request, pk=None):
        """Return single observation"""

        observation = get_object_or_404(
            ClinicalObservation.objects.select_related(
                'patient', 'patient__user', 'encounter', 'performer'
            ),
            pk=pk
        )

        # Convert to FHIR
        fhir_obs = create_fhir_observation(observation)

        # Serialize
        serializer = ObservationFHIRSerializer(fhir_obs)
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response


class FHIRConditionViewSet(viewsets.ViewSet):
    """
    FHIR Condition endpoint for diagnoses and medical problems.

    list: Return all conditions as FHIR Bundle (searchset type)
    retrieve: Return single condition as FHIR Condition resource
    """

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve all conditions as FHIR Bundle. "
                              "Supports filtering by patient, clinical status, category, and code.",
        manual_parameters=[
            openapi.Parameter(
                'patient',
                openapi.IN_QUERY,
                description="Filter by patient UUID",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'clinical-status',
                openapi.IN_QUERY,
                description="Filter by clinical status (active, inactive, resolved, etc.)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'category',
                openapi.IN_QUERY,
                description="Filter by category (problem-list-item, encounter-diagnosis)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'code',
                openapi.IN_QUERY,
                description="Filter by condition code (CIEL code)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'verification-status',
                openapi.IN_QUERY,
                description="Filter by verification status (confirmed, provisional, etc.)",
                type=openapi.TYPE_STRING
            ),
        ],
        responses={
            200: BundleSerializer,
            401: "Unauthorized"
        }
    )
    def list(self, request):
        """Return all conditions as FHIR Bundle"""

        # Start with all conditions
        conditions = ClinicalCondition.objects.select_related(
            'patient', 'patient__user', 'encounter', 'recorder', 'asserter'
        ).all()

        # Apply filters
        patient_id = request.query_params.get('patient')
        if patient_id:
            conditions = conditions.filter(patient__id=patient_id)

        clinical_status = request.query_params.get('clinical-status')
        if clinical_status:
            conditions = conditions.filter(clinical_status=clinical_status)

        category = request.query_params.get('category')
        if category:
            conditions = conditions.filter(category=category)

        code = request.query_params.get('code')
        if code:
            conditions = conditions.filter(code=code)

        verification_status = request.query_params.get('verification-status')
        if verification_status:
            conditions = conditions.filter(verification_status=verification_status)

        # Convert to FHIR resources
        fhir_conditions = [
            create_fhir_condition(cond) for cond in conditions
        ]

        # Create bundle
        bundle = create_bundle(fhir_conditions, bundle_type="searchset")

        # Serialize
        serializer = BundleSerializer(bundle)
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response

    @swagger_auto_schema(
        operation_description="Retrieve a single condition as FHIR Condition resource",
        responses={
            200: ConditionFHIRSerializer,
            404: "Condition not found",
            401: "Unauthorized"
        }
    )
    def retrieve(self, request, pk=None):
        """Return single condition"""

        condition = get_object_or_404(
            ClinicalCondition.objects.select_related(
                'patient', 'patient__user', 'encounter', 'recorder', 'asserter'
            ),
            pk=pk
        )

        # Convert to FHIR
        fhir_cond = create_fhir_condition(condition)

        # Serialize
        serializer = ConditionFHIRSerializer(fhir_cond)
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response


class FHIRMedicationRequestViewSet(viewsets.ViewSet):
    """
    FHIR MedicationRequest endpoint for prescriptions.

    list: Return all medication requests as FHIR Bundle (searchset type)
    retrieve: Return single medication request as FHIR MedicationRequest resource
    """

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve all medication requests as FHIR Bundle. "
                              "Supports filtering by patient, status, medication code, and requester.",
        manual_parameters=[
            openapi.Parameter(
                'patient',
                openapi.IN_QUERY,
                description="Filter by patient UUID",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Filter by status (active, completed, stopped, etc.)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'medication',
                openapi.IN_QUERY,
                description="Filter by medication code (CIEL code)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'requester',
                openapi.IN_QUERY,
                description="Filter by requester (doctor) UUID",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'intent',
                openapi.IN_QUERY,
                description="Filter by intent (order, plan, proposal, etc.)",
                type=openapi.TYPE_STRING
            ),
        ],
        responses={
            200: BundleSerializer,
            401: "Unauthorized"
        }
    )
    def list(self, request):
        """Return all medication requests as FHIR Bundle"""

        # Start with all medication requests
        med_requests = ClinicalMedicationRequest.objects.select_related(
            'patient', 'patient__user', 'encounter', 'requester',
            'recorder', 'source_appointment', 'reason_reference'
        ).all()

        # Apply filters
        patient_id = request.query_params.get('patient')
        if patient_id:
            med_requests = med_requests.filter(patient__id=patient_id)

        status = request.query_params.get('status')
        if status:
            med_requests = med_requests.filter(status=status)

        medication = request.query_params.get('medication')
        if medication:
            med_requests = med_requests.filter(medication_code=medication)

        requester = request.query_params.get('requester')
        if requester:
            med_requests = med_requests.filter(requester__id=requester)

        intent = request.query_params.get('intent')
        if intent:
            med_requests = med_requests.filter(intent=intent)

        # Convert to FHIR resources
        fhir_med_requests = [
            create_fhir_medication_request(mr) for mr in med_requests
        ]

        # Create bundle
        bundle = create_bundle(fhir_med_requests, bundle_type="searchset")

        # Serialize
        serializer = BundleSerializer(bundle)
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response

    @swagger_auto_schema(
        operation_description="Retrieve a single medication request as FHIR MedicationRequest resource",
        responses={
            200: MedicationRequestFHIRSerializer,
            404: "Medication request not found",
            401: "Unauthorized"
        }
    )
    def retrieve(self, request, pk=None):
        """Return single medication request"""

        med_request = get_object_or_404(
            ClinicalMedicationRequest.objects.select_related(
                'patient', 'patient__user', 'encounter', 'requester',
                'recorder', 'source_appointment', 'reason_reference'
            ),
            pk=pk
        )

        # Convert to FHIR
        fhir_med_req = create_fhir_medication_request(med_request)

        # Serialize
        serializer = MedicationRequestFHIRSerializer(fhir_med_req)
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response


class FHIRMedicationStatementViewSet(viewsets.ViewSet):
    """
    FHIR MedicationStatement endpoint for medication history.

    list: Return all medication statements as FHIR Bundle (searchset type)
    retrieve: Return single medication statement as FHIR MedicationStatement resource
    """

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve all medication statements as FHIR Bundle. "
                              "Supports filtering by patient, status, medication code, and taken status.",
        manual_parameters=[
            openapi.Parameter(
                'patient',
                openapi.IN_QUERY,
                description="Filter by patient UUID",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Filter by status (active, completed, stopped, etc.)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'medication',
                openapi.IN_QUERY,
                description="Filter by medication code (CIEL code)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'effective',
                openapi.IN_QUERY,
                description="Filter by effective date (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format='date'
            ),
        ],
        responses={
            200: BundleSerializer,
            401: "Unauthorized"
        }
    )
    def list(self, request):
        """Return all medication statements as FHIR Bundle"""

        # Start with all medication statements
        med_statements = ClinicalMedicationStatement.objects.select_related(
            'patient', 'patient__user', 'information_source',
            'based_on', 'reason_reference'
        ).all()

        # Apply filters
        patient_id = request.query_params.get('patient')
        if patient_id:
            med_statements = med_statements.filter(patient__id=patient_id)

        status = request.query_params.get('status')
        if status:
            med_statements = med_statements.filter(status=status)

        medication = request.query_params.get('medication')
        if medication:
            med_statements = med_statements.filter(medication_code=medication)

        effective = request.query_params.get('effective')
        if effective:
            med_statements = med_statements.filter(
                effective_start__lte=effective,
                effective_end__gte=effective
            ) | med_statements.filter(
                effective_start__lte=effective,
                effective_end__isnull=True
            )

        # Convert to FHIR resources
        fhir_med_statements = [
            create_fhir_medication_statement(ms) for ms in med_statements
        ]

        # Create bundle
        bundle = create_bundle(fhir_med_statements, bundle_type="searchset")

        # Serialize
        serializer = BundleSerializer(bundle)
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response

    @swagger_auto_schema(
        operation_description="Retrieve a single medication statement as FHIR MedicationStatement resource",
        responses={
            200: MedicationStatementFHIRSerializer,
            404: "Medication statement not found",
            401: "Unauthorized"
        }
    )
    def retrieve(self, request, pk=None):
        """Return single medication statement"""

        med_statement = get_object_or_404(
            ClinicalMedicationStatement.objects.select_related(
                'patient', 'patient__user', 'information_source',
                'based_on', 'reason_reference'
            ),
            pk=pk
        )

        # Convert to FHIR
        fhir_med_stmt = create_fhir_medication_statement(med_statement)

        # Serialize
        serializer = MedicationStatementFHIRSerializer(fhir_med_stmt)
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response


class FHIRAllergyIntoleranceViewSet(viewsets.ViewSet):
    """
    FHIR AllergyIntolerance endpoint for patient allergies.

    list: Return all allergies as FHIR Bundle (searchset type)
    retrieve: Return single allergy as FHIR AllergyIntolerance resource
    """

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve all allergies as FHIR Bundle. "
                              "Supports filtering by patient, clinical status, category, and criticality.",
        manual_parameters=[
            openapi.Parameter(
                'patient',
                openapi.IN_QUERY,
                description="Filter by patient UUID",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'clinical-status',
                openapi.IN_QUERY,
                description="Filter by clinical status (active, inactive, resolved)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'category',
                openapi.IN_QUERY,
                description="Filter by category (food, medication, environment, biologic)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'criticality',
                openapi.IN_QUERY,
                description="Filter by criticality (low, high, unable-to-assess)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'type',
                openapi.IN_QUERY,
                description="Filter by type (allergy, intolerance)",
                type=openapi.TYPE_STRING
            ),
        ],
        responses={
            200: BundleSerializer,
            401: "Unauthorized"
        }
    )
    def list(self, request):
        """Return all allergies as FHIR Bundle"""

        # Start with all allergies
        allergies = ClinicalAllergyIntolerance.objects.select_related(
            'patient', 'patient__user', 'recorder', 'asserter'
        ).all()

        # Apply filters
        patient_id = request.query_params.get('patient')
        if patient_id:
            allergies = allergies.filter(patient__id=patient_id)

        clinical_status = request.query_params.get('clinical-status')
        if clinical_status:
            allergies = allergies.filter(clinical_status=clinical_status)

        category = request.query_params.get('category')
        if category:
            allergies = allergies.filter(category=category)

        criticality = request.query_params.get('criticality')
        if criticality:
            allergies = allergies.filter(criticality=criticality)

        allergy_type = request.query_params.get('type')
        if allergy_type:
            allergies = allergies.filter(type=allergy_type)

        # Convert to FHIR resources
        fhir_allergies = [
            create_fhir_allergy_intolerance(allergy) for allergy in allergies
        ]

        # Create bundle
        bundle = create_bundle(fhir_allergies, bundle_type="searchset")

        # Serialize
        serializer = BundleSerializer(bundle)
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response

    @swagger_auto_schema(
        operation_description="Retrieve a single allergy as FHIR AllergyIntolerance resource",
        responses={
            200: AllergyIntoleranceFHIRSerializer,
            404: "Allergy not found",
            401: "Unauthorized"
        }
    )
    def retrieve(self, request, pk=None):
        """Return single allergy"""

        allergy = get_object_or_404(
            ClinicalAllergyIntolerance.objects.select_related(
                'patient', 'patient__user', 'recorder', 'asserter'
            ),
            pk=pk
        )

        # Convert to FHIR
        fhir_allergy = create_fhir_allergy_intolerance(allergy)

        # Serialize
        serializer = AllergyIntoleranceFHIRSerializer(fhir_allergy)
        response = Response(serializer.data)
        response["Content-Type"] = "application/fhir+json"

        return response
