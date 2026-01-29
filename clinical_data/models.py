import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import Patient
from healthcare.models import PatientDoctorAssignment, Appointment

User = get_user_model()


class ClinicalObservation(models.Model):
    """
    Stores clinical observations including vitals and symptoms.
    Maps to FHIR Observation resource.
    """

    STATUS_CHOICES = [
        ('registered', 'Registered'),
        ('preliminary', 'Preliminary'),
        ('final', 'Final'),
        ('amended', 'Amended'),
        ('corrected', 'Corrected'),
        ('cancelled', 'Cancelled'),
        ('entered-in-error', 'Entered in Error'),
        ('unknown', 'Unknown'),
    ]

    CATEGORY_CHOICES = [
        ('vital-signs', 'Vital Signs'),
        ('laboratory', 'Laboratory'),
        ('exam', 'Exam'),
        ('social-history', 'Social History'),
        ('imaging', 'Imaging'),
        ('procedure', 'Procedure'),
        ('survey', 'Survey'),
        ('therapy', 'Therapy'),
    ]

    INTERPRETATION_CHOICES = [
        ('N', 'Normal'),
        ('L', 'Low'),
        ('H', 'High'),
        ('LL', 'Critically Low'),
        ('HH', 'Critically High'),
        ('A', 'Abnormal'),
        ('<', 'Off scale low'),
        ('>', 'Off scale high'),
    ]

    SOURCE_CHOICES = [
        ('clinical_decision', 'Clinical Decision Record'),
        ('appointment', 'Appointment'),
        ('manual_entry', 'Manual Entry'),
        ('device', 'Device'),
        ('patient_report', 'Patient Report'),
    ]

    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='observations',
        help_text="Patient this observation is about"
    )
    encounter = models.ForeignKey(
        PatientDoctorAssignment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='observations',
        help_text="Healthcare encounter during which this observation was made"
    )
    performer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='performed_observations',
        help_text="Who performed or recorded the observation"
    )

    # FHIR core fields
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='final',
        help_text="Status of the observation"
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        help_text="Classification of type of observation"
    )

    # Coded observation type (CIEL/LOINC)
    code_system = models.CharField(
        max_length=255,
        help_text="Code system URL (e.g., CIEL, LOINC)"
    )
    code = models.CharField(
        max_length=50,
        help_text="Code identifying the observation (e.g., CIEL 5085 for systolic BP)"
    )
    code_display = models.CharField(
        max_length=255,
        help_text="Human-readable name of the observation"
    )

    # Value (supports multiple types)
    value_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Numeric value of the observation"
    )
    value_unit = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Unit of measurement (mmHg, bpm, mg/dL, etc.)"
    )
    value_string = models.TextField(
        null=True,
        blank=True,
        help_text="Text value for non-numeric observations"
    )
    value_code_system = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Code system for coded values"
    )
    value_code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Code value for coded observations"
    )

    # Timing
    effective_datetime = models.DateTimeField(
        help_text="When the observation was made"
    )
    issued = models.DateTimeField(
        auto_now_add=True,
        help_text="When the observation was issued/recorded"
    )

    # Reference ranges
    reference_range_low = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Lower bound of reference range"
    )
    reference_range_high = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Upper bound of reference range"
    )
    reference_range_text = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Text description of reference range"
    )

    # Interpretation
    interpretation_code = models.CharField(
        max_length=5,
        choices=INTERPRETATION_CHOICES,
        null=True,
        blank=True,
        help_text="Interpretation of the observation result"
    )

    # Method and device
    method_text = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Method used to obtain the observation"
    )
    device_text = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Device used to obtain the observation"
    )

    # Notes
    note = models.TextField(
        blank=True,
        help_text="Additional notes about the observation"
    )

    # Source tracking
    source = models.CharField(
        max_length=30,
        choices=SOURCE_CHOICES,
        help_text="Source of this observation"
    )
    source_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID of the source record"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clinical_observation'
        ordering = ['-effective_datetime']
        indexes = [
            models.Index(fields=['patient', 'category']),
            models.Index(fields=['patient', 'code']),
            models.Index(fields=['effective_datetime']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.code_display} for {self.patient.user.get_full_name()} on {self.effective_datetime.date()}"


class ClinicalCondition(models.Model):
    """
    Stores diagnoses and medical problems.
    Maps to FHIR Condition resource.
    """

    CLINICAL_STATUS_CHOICES = [
        ('active', 'Active'),
        ('recurrence', 'Recurrence'),
        ('relapse', 'Relapse'),
        ('inactive', 'Inactive'),
        ('remission', 'Remission'),
        ('resolved', 'Resolved'),
    ]

    VERIFICATION_STATUS_CHOICES = [
        ('unconfirmed', 'Unconfirmed'),
        ('provisional', 'Provisional'),
        ('differential', 'Differential'),
        ('confirmed', 'Confirmed'),
        ('refuted', 'Refuted'),
        ('entered-in-error', 'Entered in Error'),
    ]

    CATEGORY_CHOICES = [
        ('problem-list-item', 'Problem List Item'),
        ('encounter-diagnosis', 'Encounter Diagnosis'),
    ]

    SEVERITY_CHOICES = [
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
    ]

    SOURCE_CHOICES = [
        ('appointment_diagnosis', 'Appointment Diagnosis'),
        ('patient_history', 'Patient History'),
        ('referral', 'Referral'),
        ('manual_entry', 'Manual Entry'),
    ]

    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='conditions',
        help_text="Patient who has the condition"
    )
    encounter = models.ForeignKey(
        PatientDoctorAssignment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conditions',
        help_text="Encounter during which the condition was diagnosed"
    )
    recorder = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_conditions',
        help_text="Who recorded the condition"
    )
    asserter = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asserted_conditions',
        help_text="Who made the diagnosis"
    )

    # FHIR core fields
    clinical_status = models.CharField(
        max_length=20,
        choices=CLINICAL_STATUS_CHOICES,
        default='active',
        help_text="Clinical status of the condition"
    )
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='confirmed',
        help_text="Verification status of the condition"
    )
    category = models.CharField(
        max_length=25,
        choices=CATEGORY_CHOICES,
        default='problem-list-item',
        help_text="Category of the condition"
    )

    # Coded condition (CIEL primary, ICD-10 secondary)
    code_system = models.CharField(
        max_length=255,
        help_text="Primary code system URL (CIEL)"
    )
    code = models.CharField(
        max_length=50,
        help_text="CIEL code for the condition"
    )
    code_display = models.CharField(
        max_length=255,
        help_text="Human-readable name of the condition"
    )

    # Secondary coding (ICD-10 for billing)
    icd10_code = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="ICD-10 code"
    )
    icd10_display = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="ICD-10 description"
    )

    # Severity
    severity_code = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        null=True,
        blank=True,
        help_text="Severity of the condition"
    )

    # Onset
    onset_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the condition started"
    )
    onset_age = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(150)],
        help_text="Age when condition started"
    )
    onset_string = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Text description of onset (e.g., 'since childhood')"
    )

    # Resolution
    abatement_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the condition resolved"
    )

    # Recording details
    recorded_date = models.DateField(
        help_text="When the condition was first recorded"
    )

    # Notes
    note = models.TextField(
        blank=True,
        help_text="Additional notes about the condition"
    )

    # Source tracking
    source = models.CharField(
        max_length=30,
        choices=SOURCE_CHOICES,
        help_text="Source of this condition record"
    )
    source_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID of the source record"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clinical_condition'
        ordering = ['-recorded_date']
        indexes = [
            models.Index(fields=['patient', 'clinical_status']),
            models.Index(fields=['patient', 'category']),
            models.Index(fields=['code']),
            models.Index(fields=['icd10_code']),
        ]

    def __str__(self):
        return f"{self.code_display} - {self.patient.user.get_full_name()} ({self.clinical_status})"


class ClinicalMedicationRequest(models.Model):
    """
    Stores medication prescriptions.
    Maps to FHIR MedicationRequest resource.
    """

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('on-hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('entered-in-error', 'Entered in Error'),
        ('stopped', 'Stopped'),
        ('draft', 'Draft'),
        ('unknown', 'Unknown'),
    ]

    INTENT_CHOICES = [
        ('proposal', 'Proposal'),
        ('plan', 'Plan'),
        ('order', 'Order'),
        ('original-order', 'Original Order'),
        ('reflex-order', 'Reflex Order'),
        ('filler-order', 'Filler Order'),
        ('instance-order', 'Instance Order'),
        ('option', 'Option'),
    ]

    PERIOD_CHOICES = [
        ('day', 'Day'),
        ('week', 'Week'),
        ('month', 'Month'),
    ]

    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='medication_requests',
        help_text="Patient for whom medication is prescribed"
    )
    encounter = models.ForeignKey(
        PatientDoctorAssignment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medication_requests',
        help_text="Encounter during which medication was prescribed"
    )
    requester = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='medication_requests',
        help_text="Doctor who prescribed the medication"
    )
    recorder = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_prescriptions',
        help_text="Person who recorded the prescription"
    )
    source_appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medication_requests',
        help_text="Appointment during which medication was prescribed"
    )
    reason_reference = models.ForeignKey(
        'ClinicalCondition',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medication_requests',
        help_text="Condition being treated"
    )

    # FHIR core fields
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Status of the prescription"
    )
    intent = models.CharField(
        max_length=20,
        choices=INTENT_CHOICES,
        default='order',
        help_text="Intent of the prescription"
    )

    # Medication (CIEL coding)
    medication_code_system = models.CharField(
        max_length=255,
        help_text="Medication code system URL"
    )
    medication_code = models.CharField(
        max_length=50,
        help_text="CIEL code for the medication"
    )
    medication_display = models.CharField(
        max_length=255,
        help_text="Medication name"
    )
    medication_text = models.CharField(
        max_length=255,
        help_text="Free text medication name"
    )

    # Dosage details
    dosage_text = models.CharField(
        max_length=500,
        help_text="Complete dosage instructions (e.g., 'Take 1 tablet by mouth daily')"
    )
    dosage_route = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Route of administration (oral, IV, topical, etc.)"
    )
    dosage_timing_frequency = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Number of times per period (e.g., 3 times per day)"
    )
    dosage_timing_period = models.CharField(
        max_length=10,
        choices=PERIOD_CHOICES,
        default='day',
        help_text="Period unit (day, week, month)"
    )
    dosage_timing_duration = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="How many days to take the medication"
    )

    # Dose amount
    dose_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Dose quantity (e.g., 10)"
    )
    dose_unit = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Dose unit (e.g., mg, ml)"
    )

    # Quantity and refills
    quantity_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Quantity to dispense (e.g., 30)"
    )
    quantity_unit = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Quantity unit (e.g., tablets, ml)"
    )
    refills = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of refills authorized"
    )

    # Dates
    authored_on = models.DateTimeField(
        auto_now_add=True,
        help_text="When the prescription was written"
    )
    validity_period_start = models.DateField(
        null=True,
        blank=True,
        help_text="When prescription becomes valid"
    )
    validity_period_end = models.DateField(
        null=True,
        blank=True,
        help_text="When prescription expires"
    )

    # Reason
    reason_code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Code for reason (e.g., ICD-10)"
    )
    reason_text = models.TextField(
        null=True,
        blank=True,
        help_text="Text description of reason"
    )

    # Instructions
    patient_instruction = models.TextField(
        blank=True,
        help_text="Instructions for the patient"
    )
    note = models.TextField(
        blank=True,
        help_text="Additional notes"
    )

    # Substitution
    substitution_allowed = models.BooleanField(
        default=True,
        help_text="Whether generic substitution is allowed"
    )
    substitution_reason = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Reason for substitution preference"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clinical_medication_request'
        ordering = ['-authored_on']
        indexes = [
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['requester']),
            models.Index(fields=['medication_code']),
        ]

    def __str__(self):
        return f"{self.medication_display} for {self.patient.user.get_full_name()}"


class ClinicalMedicationStatement(models.Model):
    """
    Stores medication history (what patient is taking or has taken).
    Maps to FHIR MedicationStatement resource.
    """

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('entered-in-error', 'Entered in Error'),
        ('intended', 'Intended'),
        ('stopped', 'Stopped'),
        ('on-hold', 'On Hold'),
        ('unknown', 'Unknown'),
        ('not-taken', 'Not Taken'),
    ]

    TAKEN_CHOICES = [
        ('y', 'Yes'),
        ('n', 'No'),
        ('unk', 'Unknown'),
    ]

    SOURCE_CHOICES = [
        ('patient_history', 'Patient History'),
        ('patient_report', 'Patient Report'),
        ('prescription', 'Prescription'),
        ('manual_entry', 'Manual Entry'),
    ]

    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='medication_statements',
        help_text="Patient taking the medication"
    )
    information_source = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reported_medication_statements',
        help_text="Who reported this medication"
    )
    based_on = models.ForeignKey(
        'ClinicalMedicationRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='statements',
        help_text="Prescription this statement is based on"
    )
    reason_reference = models.ForeignKey(
        'ClinicalCondition',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medication_statements',
        help_text="Condition being treated"
    )

    # FHIR core fields
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Status of the medication statement"
    )

    # Medication (CIEL coding)
    medication_code_system = models.CharField(
        max_length=255,
        help_text="Medication code system URL"
    )
    medication_code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="CIEL code (may be unknown if patient-reported)"
    )
    medication_display = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Medication name"
    )
    medication_text = models.CharField(
        max_length=255,
        help_text="Free text medication name (always required)"
    )

    # Taken or not
    taken = models.CharField(
        max_length=3,
        choices=TAKEN_CHOICES,
        default='y',
        help_text="Whether medication is being taken"
    )

    # Timing
    effective_start = models.DateField(
        null=True,
        blank=True,
        help_text="When patient started taking the medication"
    )
    effective_end = models.DateField(
        null=True,
        blank=True,
        help_text="When patient stopped taking the medication"
    )
    date_asserted = models.DateTimeField(
        auto_now_add=True,
        help_text="When this statement was recorded"
    )

    # Dosage (as patient describes it)
    dosage_text = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Dosage as reported by patient"
    )
    dosage_as_needed = models.BooleanField(
        default=False,
        help_text="Whether medication is taken as needed (PRN)"
    )

    # Reason
    reason_code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Code for reason medication is taken"
    )
    reason_text = models.TextField(
        null=True,
        blank=True,
        help_text="Why patient is taking this medication"
    )

    # Notes
    note = models.TextField(
        blank=True,
        help_text="Additional notes"
    )

    # Source tracking
    source = models.CharField(
        max_length=30,
        choices=SOURCE_CHOICES,
        help_text="Source of this statement"
    )
    source_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID of the source record"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clinical_medication_statement'
        ordering = ['-date_asserted']
        indexes = [
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['patient', 'taken']),
            models.Index(fields=['medication_code']),
        ]

    def __str__(self):
        return f"{self.medication_text} - {self.patient.user.get_full_name()} ({self.status})"


class ClinicalAllergyIntolerance(models.Model):
    """
    Stores allergies and intolerances (critical for patient safety).
    Maps to FHIR AllergyIntolerance resource.
    """

    CLINICAL_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('resolved', 'Resolved'),
    ]

    VERIFICATION_STATUS_CHOICES = [
        ('unconfirmed', 'Unconfirmed'),
        ('confirmed', 'Confirmed'),
        ('refuted', 'Refuted'),
        ('entered-in-error', 'Entered in Error'),
    ]

    TYPE_CHOICES = [
        ('allergy', 'Allergy'),
        ('intolerance', 'Intolerance'),
    ]

    CATEGORY_CHOICES = [
        ('food', 'Food'),
        ('medication', 'Medication'),
        ('environment', 'Environment'),
        ('biologic', 'Biologic'),
    ]

    CRITICALITY_CHOICES = [
        ('low', 'Low Risk'),
        ('high', 'High Risk'),
        ('unable-to-assess', 'Unable to Assess'),
    ]

    SOURCE_CHOICES = [
        ('patient_history', 'Patient History'),
        ('patient_report', 'Patient Report'),
        ('clinical_observation', 'Clinical Observation'),
        ('manual_entry', 'Manual Entry'),
    ]

    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='allergy_intolerances',
        help_text="Patient who has the allergy/intolerance"
    )
    recorder = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_allergies',
        help_text="Who recorded this allergy"
    )
    asserter = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asserted_allergies',
        help_text="Source of the information (patient, provider)"
    )

    # FHIR core fields
    clinical_status = models.CharField(
        max_length=20,
        choices=CLINICAL_STATUS_CHOICES,
        default='active',
        help_text="Clinical status"
    )
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='unconfirmed',
        help_text="Verification status"
    )
    type = models.CharField(
        max_length=15,
        choices=TYPE_CHOICES,
        default='allergy',
        help_text="Type (allergy vs intolerance)"
    )
    category = models.CharField(
        max_length=15,
        choices=CATEGORY_CHOICES,
        help_text="Category of allergen"
    )
    criticality = models.CharField(
        max_length=20,
        choices=CRITICALITY_CHOICES,
        null=True,
        blank=True,
        help_text="Potential clinical harm"
    )

    # Allergen coding (CIEL)
    code_system = models.CharField(
        max_length=255,
        help_text="Code system URL (CIEL)"
    )
    code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="CIEL code for the allergen"
    )
    code_display = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Allergen name"
    )
    code_text = models.CharField(
        max_length=255,
        help_text="Free text allergen description (always required)"
    )

    # Onset
    onset_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When allergy first occurred"
    )
    onset_age = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(150)],
        help_text="Age when allergy first occurred"
    )
    onset_string = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Text description of onset"
    )

    # Recording details
    recorded_date = models.DateTimeField(
        auto_now_add=True,
        help_text="When this allergy was recorded"
    )
    last_occurrence = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the reaction last occurred"
    )

    # Reaction details (stored as JSON)
    reactions = models.JSONField(
        default=list,
        blank=True,
        help_text="Array of reaction details"
    )
    # Structure: [
    #   {
    #     "substance_text": "Penicillin",
    #     "manifestation_code": "CIEL code",
    #     "manifestation_text": "Rash",
    #     "severity": "severe",
    #     "description": "Developed widespread rash",
    #     "onset": "2023-01-15T10:30:00Z"
    #   }
    # ]

    # Notes
    note = models.TextField(
        blank=True,
        help_text="Additional notes"
    )

    # Source tracking
    source = models.CharField(
        max_length=30,
        choices=SOURCE_CHOICES,
        help_text="Source of this allergy record"
    )
    source_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID of the source record"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clinical_allergy_intolerance'
        ordering = ['-recorded_date']
        indexes = [
            models.Index(fields=['patient', 'clinical_status']),
            models.Index(fields=['patient', 'category']),
            models.Index(fields=['patient', 'criticality']),
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return f"{self.code_text} - {self.patient.user.get_full_name()} ({self.criticality or 'unknown risk'})"


class MigrationAudit(models.Model):
    """
    Tracks data migrations from text fields to structured FHIR resources.
    Enables reversibility and manual review of automated migrations.
    """

    SOURCE_MODEL_CHOICES = [
        ('Patient', 'Patient'),
        ('ClinicalDecisionRecord', 'Clinical Decision Record'),
        ('Appointment', 'Appointment'),
    ]

    TARGET_MODEL_CHOICES = [
        ('ClinicalObservation', 'Clinical Observation'),
        ('ClinicalCondition', 'Clinical Condition'),
        ('ClinicalMedicationRequest', 'Clinical Medication Request'),
        ('ClinicalMedicationStatement', 'Clinical Medication Statement'),
        ('ClinicalAllergyIntolerance', 'Clinical Allergy Intolerance'),
    ]

    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Source information
    source_model = models.CharField(
        max_length=50,
        choices=SOURCE_MODEL_CHOICES,
        help_text="Model where data originated"
    )
    source_field = models.CharField(
        max_length=100,
        help_text="Field name in source model"
    )
    source_value = models.TextField(
        help_text="Original value before migration"
    )
    source_record_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID of the source record"
    )

    # Target information
    target_model = models.CharField(
        max_length=50,
        choices=TARGET_MODEL_CHOICES,
        help_text="Model where data was migrated to"
    )
    target_id = models.UUIDField(
        help_text="ID of the created record"
    )

    # Migration metadata
    confidence_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Confidence score for automated code assignment (0.0-1.0)"
    )
    migration_method = models.CharField(
        max_length=50,
        default='automated',
        help_text="Method used for migration (automated, manual, reviewed)"
    )

    # Review tracking
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_migrations',
        help_text="User who reviewed this migration"
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the migration was reviewed"
    )
    approved = models.BooleanField(
        default=False,
        help_text="Whether the migration was approved"
    )
    review_notes = models.TextField(
        blank=True,
        help_text="Notes from manual review"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'migration_audit'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['source_model', 'source_field']),
            models.Index(fields=['target_model', 'target_id']),
            models.Index(fields=['approved']),
            models.Index(fields=['confidence_score']),
        ]

    def __str__(self):
        return f"{self.source_model}.{self.source_field} → {self.target_model} (confidence: {self.confidence_score})"
