"""
FHIR Adapters - Convert Django models to FHIR R4 resources

These adapter functions transform our Django clinical data models into
FHIR-compliant resource representations using the fhir.resources library.
"""

from fhir.resources.observation import Observation as FHIRObservation
from fhir.resources.condition import Condition as FHIRCondition
from fhir.resources.medicationrequest import MedicationRequest as FHIRMedicationRequest
from fhir.resources.medicationstatement import MedicationStatement as FHIRMedicationStatement
from fhir.resources.allergyintolerance import AllergyIntolerance as FHIRAllergyIntolerance
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.quantity import Quantity
from fhir.resources.reference import Reference
from fhir.resources.identifier import Identifier
from fhir.resources.meta import Meta
from fhir.resources.annotation import Annotation
from fhir.resources.range import Range
from fhir.resources.dosage import Dosage
from fhir.resources.timing import Timing
from fhir.resources.duration import Duration
from fhir.resources.period import Period


def create_fhir_observation(clinical_obs):
    """
    Convert ClinicalObservation model to FHIR Observation resource.

    Args:
        clinical_obs: ClinicalObservation model instance

    Returns:
        FHIRObservation: FHIR Observation resource
    """
    fhir_obs = FHIRObservation()

    # Basic identification
    fhir_obs.id = str(clinical_obs.id)
    fhir_obs.meta = Meta(
        profile=["http://hl7.org/fhir/StructureDefinition/Observation"]
    )

    # Identifiers
    fhir_obs.identifier = [
        Identifier(
            system="urn:panacare:observation",
            value=str(clinical_obs.id)
        )
    ]

    # Status
    fhir_obs.status = clinical_obs.status

    # Category
    fhir_obs.category = [
        CodeableConcept(
            coding=[
                Coding(
                    system="http://terminology.hl7.org/CodeSystem/observation-category",
                    code=clinical_obs.category,
                    display=clinical_obs.get_category_display()
                )
            ]
        )
    ]

    # Code (what was observed) - CIEL coding
    fhir_obs.code = CodeableConcept(
        coding=[
            Coding(
                system=clinical_obs.code_system,
                code=clinical_obs.code,
                display=clinical_obs.code_display
            )
        ],
        text=clinical_obs.code_display
    )

    # Subject (patient reference)
    fhir_obs.subject = Reference(
        reference=f"Patient/{clinical_obs.patient.id}",
        display=clinical_obs.patient.user.get_full_name() or clinical_obs.patient.user.username
    )

    # Encounter context (if available)
    if clinical_obs.encounter:
        fhir_obs.encounter = Reference(
            reference=f"Encounter/{clinical_obs.encounter.id}"
        )

    # Timing
    fhir_obs.effectiveDateTime = clinical_obs.effective_datetime.isoformat()
    fhir_obs.issued = clinical_obs.issued.isoformat()

    # Value - supports multiple types
    if clinical_obs.value_quantity is not None:
        fhir_obs.valueQuantity = Quantity(
            value=float(clinical_obs.value_quantity),
            unit=clinical_obs.value_unit,
            system="http://unitsofmeasure.org",
            code=clinical_obs.value_unit
        )
    elif clinical_obs.value_string:
        fhir_obs.valueString = clinical_obs.value_string
    elif clinical_obs.value_code:
        fhir_obs.valueCodeableConcept = CodeableConcept(
            coding=[
                Coding(
                    system=clinical_obs.value_code_system,
                    code=clinical_obs.value_code
                )
            ]
        )

    # Reference range
    if clinical_obs.reference_range_low is not None or clinical_obs.reference_range_high is not None:
        range_dict = {}

        if clinical_obs.reference_range_low is not None:
            range_dict["low"] = {
                "value": float(clinical_obs.reference_range_low),
                "unit": clinical_obs.value_unit,
                "system": "http://unitsofmeasure.org",
                "code": clinical_obs.value_unit
            }

        if clinical_obs.reference_range_high is not None:
            range_dict["high"] = {
                "value": float(clinical_obs.reference_range_high),
                "unit": clinical_obs.value_unit,
                "system": "http://unitsofmeasure.org",
                "code": clinical_obs.value_unit
            }

        if clinical_obs.reference_range_text:
            range_dict["text"] = clinical_obs.reference_range_text

        fhir_obs.referenceRange = [range_dict]

    # Interpretation
    if clinical_obs.interpretation_code:
        fhir_obs.interpretation = [
            CodeableConcept(
                coding=[
                    Coding(
                        system="http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                        code=clinical_obs.interpretation_code,
                        display=clinical_obs.get_interpretation_code_display()
                    )
                ]
            )
        ]

    # Performer (who recorded/performed the observation)
    if clinical_obs.performer:
        fhir_obs.performer = [
            Reference(
                reference=f"Practitioner/{clinical_obs.performer.id}",
                display=clinical_obs.performer.get_full_name() or clinical_obs.performer.username
            )
        ]

    # Method
    if clinical_obs.method_text:
        fhir_obs.method = CodeableConcept(text=clinical_obs.method_text)

    # Device
    if clinical_obs.device_text:
        fhir_obs.device = Reference(display=clinical_obs.device_text)

    # Notes
    if clinical_obs.note:
        fhir_obs.note = [
            Annotation(text=clinical_obs.note)
        ]

    return fhir_obs


def create_fhir_condition(clinical_condition):
    """
    Convert ClinicalCondition model to FHIR Condition resource.

    Args:
        clinical_condition: ClinicalCondition model instance

    Returns:
        FHIRCondition: FHIR Condition resource
    """
    fhir_cond = FHIRCondition()

    # Basic identification
    fhir_cond.id = str(clinical_condition.id)
    fhir_cond.meta = Meta(
        profile=["http://hl7.org/fhir/StructureDefinition/Condition"]
    )

    # Identifiers
    fhir_cond.identifier = [
        Identifier(
            system="urn:panacare:condition",
            value=str(clinical_condition.id)
        )
    ]

    # Clinical status
    fhir_cond.clinicalStatus = CodeableConcept(
        coding=[
            Coding(
                system="http://terminology.hl7.org/CodeSystem/condition-clinical",
                code=clinical_condition.clinical_status,
                display=clinical_condition.get_clinical_status_display()
            )
        ]
    )

    # Verification status
    fhir_cond.verificationStatus = CodeableConcept(
        coding=[
            Coding(
                system="http://terminology.hl7.org/CodeSystem/condition-ver-status",
                code=clinical_condition.verification_status,
                display=clinical_condition.get_verification_status_display()
            )
        ]
    )

    # Category
    fhir_cond.category = [
        CodeableConcept(
            coding=[
                Coding(
                    system="http://terminology.hl7.org/CodeSystem/condition-category",
                    code=clinical_condition.category,
                    display=clinical_condition.get_category_display()
                )
            ]
        )
    ]

    # Severity
    if clinical_condition.severity_code:
        fhir_cond.severity = CodeableConcept(
            coding=[
                Coding(
                    system="http://snomed.info/sct",
                    code={
                        'mild': '255604002',
                        'moderate': '6736007',
                        'severe': '24484000'
                    }.get(clinical_condition.severity_code),
                    display=clinical_condition.get_severity_code_display()
                )
            ]
        )

    # Code (CIEL primary, ICD-10 secondary)
    codings = [
        Coding(
            system=clinical_condition.code_system,
            code=clinical_condition.code,
            display=clinical_condition.code_display
        )
    ]

    # Add ICD-10 as secondary coding if available
    if clinical_condition.icd10_code:
        codings.append(
            Coding(
                system="http://hl7.org/fhir/sid/icd-10-cm",
                code=clinical_condition.icd10_code,
                display=clinical_condition.icd10_display or clinical_condition.code_display
            )
        )

    fhir_cond.code = CodeableConcept(
        coding=codings,
        text=clinical_condition.code_display
    )

    # Subject (patient reference)
    fhir_cond.subject = Reference(
        reference=f"Patient/{clinical_condition.patient.id}",
        display=clinical_condition.patient.user.get_full_name() or clinical_condition.patient.user.username
    )

    # Encounter
    if clinical_condition.encounter:
        fhir_cond.encounter = Reference(
            reference=f"Encounter/{clinical_condition.encounter.id}"
        )

    # Onset (multiple types supported)
    if clinical_condition.onset_datetime:
        fhir_cond.onsetDateTime = clinical_condition.onset_datetime.isoformat()
    elif clinical_condition.onset_age is not None:
        fhir_cond.onsetAge = Quantity(
            value=clinical_condition.onset_age,
            unit="years",
            system="http://unitsofmeasure.org",
            code="a"
        )
    elif clinical_condition.onset_string:
        fhir_cond.onsetString = clinical_condition.onset_string

    # Abatement (resolution)
    if clinical_condition.abatement_datetime:
        fhir_cond.abatementDateTime = clinical_condition.abatement_datetime.isoformat()

    # Recorded date
    fhir_cond.recordedDate = clinical_condition.recorded_date.isoformat()

    # Recorder
    if clinical_condition.recorder:
        fhir_cond.recorder = Reference(
            reference=f"Practitioner/{clinical_condition.recorder.id}",
            display=clinical_condition.recorder.get_full_name() or clinical_condition.recorder.username
        )

    # Asserter (who diagnosed)
    if clinical_condition.asserter:
        fhir_cond.asserter = Reference(
            reference=f"Practitioner/{clinical_condition.asserter.id}",
            display=clinical_condition.asserter.get_full_name() or clinical_condition.asserter.username
        )

    # Notes
    if clinical_condition.note:
        fhir_cond.note = [
            Annotation(text=clinical_condition.note)
        ]

    return fhir_cond


def create_fhir_medication_request(med_request):
    """
    Convert ClinicalMedicationRequest model to FHIR MedicationRequest resource.

    Args:
        med_request: ClinicalMedicationRequest model instance

    Returns:
        FHIRMedicationRequest: FHIR MedicationRequest resource
    """
    fhir_med_req = FHIRMedicationRequest()

    # Basic identification
    fhir_med_req.id = str(med_request.id)
    fhir_med_req.meta = Meta(
        profile=["http://hl7.org/fhir/StructureDefinition/MedicationRequest"]
    )

    # Identifiers
    fhir_med_req.identifier = [
        Identifier(
            system="urn:panacare:medication-request",
            value=str(med_request.id)
        )
    ]

    # Status
    fhir_med_req.status = med_request.status

    # Intent
    fhir_med_req.intent = med_request.intent

    # Medication (CIEL coding)
    fhir_med_req.medicationCodeableConcept = CodeableConcept(
        coding=[
            Coding(
                system=med_request.medication_code_system,
                code=med_request.medication_code,
                display=med_request.medication_display
            )
        ],
        text=med_request.medication_text
    )

    # Subject (patient)
    fhir_med_req.subject = Reference(
        reference=f"Patient/{med_request.patient.id}",
        display=med_request.patient.user.get_full_name() or med_request.patient.user.username
    )

    # Encounter
    if med_request.encounter:
        fhir_med_req.encounter = Reference(
            reference=f"Encounter/{med_request.encounter.id}"
        )

    # Authored on
    fhir_med_req.authoredOn = med_request.authored_on.isoformat()

    # Requester (prescribing doctor)
    fhir_med_req.requester = Reference(
        reference=f"Practitioner/{med_request.requester.id}",
        display=med_request.requester.get_full_name() or med_request.requester.username
    )

    # Recorder
    if med_request.recorder:
        fhir_med_req.recorder = Reference(
            reference=f"Practitioner/{med_request.recorder.id}",
            display=med_request.recorder.get_full_name() or med_request.recorder.username
        )

    # Reason (condition being treated)
    reason_code_list = []
    if med_request.reason_text:
        reason_code_list.append(
            CodeableConcept(text=med_request.reason_text)
        )
    if med_request.reason_reference:
        fhir_med_req.reasonReference = [
            Reference(
                reference=f"Condition/{med_request.reason_reference.id}",
                display=med_request.reason_reference.code_display
            )
        ]
    if reason_code_list:
        fhir_med_req.reasonCode = reason_code_list

    # Dosage instruction
    dosage = Dosage()
    dosage.text = med_request.dosage_text

    if med_request.dosage_route:
        dosage.route = CodeableConcept(text=med_request.dosage_route)

    # Timing
    timing = Timing()
    timing.repeat = {
        "frequency": med_request.dosage_timing_frequency,
        "period": 1,
        "periodUnit": med_request.dosage_timing_period
    }
    if med_request.dosage_timing_duration:
        timing.repeat["duration"] = med_request.dosage_timing_duration
        timing.repeat["durationUnit"] = "d"  # days

    dosage.timing = timing

    # Dose quantity
    if med_request.dose_value:
        dosage.doseAndRate = [{
            "doseQuantity": {
                "value": float(med_request.dose_value),
                "unit": med_request.dose_unit,
                "system": "http://unitsofmeasure.org",
                "code": med_request.dose_unit
            }
        }]

    fhir_med_req.dosageInstruction = [dosage]

    # Dispense request
    if med_request.quantity_value:
        dispense_request = {
            "quantity": {
                "value": float(med_request.quantity_value),
                "unit": med_request.quantity_unit,
                "system": "http://unitsofmeasure.org",
                "code": med_request.quantity_unit
            }
        }

        if med_request.refills > 0:
            dispense_request["numberOfRepeatsAllowed"] = med_request.refills

        if med_request.validity_period_start or med_request.validity_period_end:
            validity_period = {}
            if med_request.validity_period_start:
                validity_period["start"] = med_request.validity_period_start.isoformat()
            if med_request.validity_period_end:
                validity_period["end"] = med_request.validity_period_end.isoformat()
            dispense_request["validityPeriod"] = validity_period

        fhir_med_req.dispenseRequest = dispense_request

    # Substitution
    if not med_request.substitution_allowed or med_request.substitution_reason:
        substitution = {
            "allowedBoolean": med_request.substitution_allowed
        }
        if med_request.substitution_reason:
            substitution["reason"] = CodeableConcept(text=med_request.substitution_reason)
        fhir_med_req.substitution = substitution

    # Patient instructions
    if med_request.patient_instruction:
        # Add to dosage instruction
        if fhir_med_req.dosageInstruction:
            fhir_med_req.dosageInstruction[0].patientInstruction = med_request.patient_instruction

    # Notes
    if med_request.note:
        fhir_med_req.note = [
            Annotation(text=med_request.note)
        ]

    return fhir_med_req


def create_fhir_medication_statement(med_statement):
    """
    Convert ClinicalMedicationStatement model to FHIR MedicationStatement resource.

    Args:
        med_statement: ClinicalMedicationStatement model instance

    Returns:
        FHIRMedicationStatement: FHIR MedicationStatement resource
    """
    fhir_med_stmt = FHIRMedicationStatement()

    # Basic identification
    fhir_med_stmt.id = str(med_statement.id)
    fhir_med_stmt.meta = Meta(
        profile=["http://hl7.org/fhir/StructureDefinition/MedicationStatement"]
    )

    # Identifiers
    fhir_med_stmt.identifier = [
        Identifier(
            system="urn:panacare:medication-statement",
            value=str(med_statement.id)
        )
    ]

    # Status
    fhir_med_stmt.status = med_statement.status

    # Medication (CIEL coding when available)
    codings = []
    if med_statement.medication_code:
        codings.append(
            Coding(
                system=med_statement.medication_code_system,
                code=med_statement.medication_code,
                display=med_statement.medication_display
            )
        )

    fhir_med_stmt.medicationCodeableConcept = CodeableConcept(
        coding=codings if codings else None,
        text=med_statement.medication_text
    )

    # Subject (patient)
    fhir_med_stmt.subject = Reference(
        reference=f"Patient/{med_statement.patient.id}",
        display=med_statement.patient.user.get_full_name() or med_statement.patient.user.username
    )

    # Effective period (when taking medication)
    if med_statement.effective_start or med_statement.effective_end:
        effective_period = {}
        if med_statement.effective_start:
            effective_period["start"] = med_statement.effective_start.isoformat()
        if med_statement.effective_end:
            effective_period["end"] = med_statement.effective_end.isoformat()
        fhir_med_stmt.effectivePeriod = effective_period

    # Date asserted
    fhir_med_stmt.dateAsserted = med_statement.date_asserted.isoformat()

    # Information source (who reported)
    if med_statement.information_source:
        fhir_med_stmt.informationSource = Reference(
            reference=f"Practitioner/{med_statement.information_source.id}",
            display=med_statement.information_source.get_full_name() or med_statement.information_source.username
        )

    # Based on (prescription reference)
    if med_statement.based_on:
        fhir_med_stmt.basedOn = [
            Reference(
                reference=f"MedicationRequest/{med_statement.based_on.id}",
                display=med_statement.based_on.medication_display
            )
        ]

    # Reason (condition being treated)
    if med_statement.reason_text or med_statement.reason_reference:
        reason_code_list = []
        if med_statement.reason_text:
            reason_code_list.append(
                CodeableConcept(text=med_statement.reason_text)
            )
        if reason_code_list:
            fhir_med_stmt.reasonCode = reason_code_list

        if med_statement.reason_reference:
            fhir_med_stmt.reasonReference = [
                Reference(
                    reference=f"Condition/{med_statement.reason_reference.id}",
                    display=med_statement.reason_reference.code_display
                )
            ]

    # Dosage (as patient describes)
    if med_statement.dosage_text:
        dosage = Dosage()
        dosage.text = med_statement.dosage_text
        dosage.asNeededBoolean = med_statement.dosage_as_needed
        fhir_med_stmt.dosage = [dosage]

    # Notes
    if med_statement.note:
        fhir_med_stmt.note = [
            Annotation(text=med_statement.note)
        ]

    return fhir_med_stmt


def create_fhir_allergy_intolerance(allergy):
    """
    Convert ClinicalAllergyIntolerance model to FHIR AllergyIntolerance resource.

    Args:
        allergy: ClinicalAllergyIntolerance model instance

    Returns:
        FHIRAllergyIntolerance: FHIR AllergyIntolerance resource
    """
    fhir_allergy = FHIRAllergyIntolerance()

    # Basic identification
    fhir_allergy.id = str(allergy.id)
    fhir_allergy.meta = Meta(
        profile=["http://hl7.org/fhir/StructureDefinition/AllergyIntolerance"]
    )

    # Identifiers
    fhir_allergy.identifier = [
        Identifier(
            system="urn:panacare:allergy-intolerance",
            value=str(allergy.id)
        )
    ]

    # Clinical status
    fhir_allergy.clinicalStatus = CodeableConcept(
        coding=[
            Coding(
                system="http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
                code=allergy.clinical_status,
                display=allergy.get_clinical_status_display()
            )
        ]
    )

    # Verification status
    fhir_allergy.verificationStatus = CodeableConcept(
        coding=[
            Coding(
                system="http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
                code=allergy.verification_status,
                display=allergy.get_verification_status_display()
            )
        ]
    )

    # Type
    fhir_allergy.type = allergy.type

    # Category
    fhir_allergy.category = [allergy.category]

    # Criticality
    if allergy.criticality:
        fhir_allergy.criticality = allergy.criticality

    # Code (allergen with CIEL coding when available)
    codings = []
    if allergy.code:
        codings.append(
            Coding(
                system=allergy.code_system,
                code=allergy.code,
                display=allergy.code_display
            )
        )

    fhir_allergy.code = CodeableConcept(
        coding=codings if codings else None,
        text=allergy.code_text
    )

    # Patient
    fhir_allergy.patient = Reference(
        reference=f"Patient/{allergy.patient.id}",
        display=allergy.patient.user.get_full_name() or allergy.patient.user.username
    )

    # Onset (multiple types supported)
    if allergy.onset_datetime:
        fhir_allergy.onsetDateTime = allergy.onset_datetime.isoformat()
    elif allergy.onset_age is not None:
        fhir_allergy.onsetAge = Quantity(
            value=allergy.onset_age,
            unit="years",
            system="http://unitsofmeasure.org",
            code="a"
        )
    elif allergy.onset_string:
        fhir_allergy.onsetString = allergy.onset_string

    # Recorded date
    fhir_allergy.recordedDate = allergy.recorded_date.isoformat()

    # Recorder
    if allergy.recorder:
        fhir_allergy.recorder = Reference(
            reference=f"Practitioner/{allergy.recorder.id}",
            display=allergy.recorder.get_full_name() or allergy.recorder.username
        )

    # Asserter (source of information)
    if allergy.asserter:
        fhir_allergy.asserter = Reference(
            reference=f"Practitioner/{allergy.asserter.id}",
            display=allergy.asserter.get_full_name() or allergy.asserter.username
        )

    # Last occurrence
    if allergy.last_occurrence:
        fhir_allergy.lastOccurrence = allergy.last_occurrence.isoformat()

    # Reactions
    if allergy.reactions:
        fhir_reactions = []
        for reaction in allergy.reactions:
            fhir_reaction = {}

            # Substance
            if reaction.get('substance_text'):
                fhir_reaction['substance'] = CodeableConcept(
                    text=reaction['substance_text']
                )

            # Manifestation (what happened)
            manifestation_codings = []
            if reaction.get('manifestation_code'):
                manifestation_codings.append(
                    Coding(
                        system=allergy.code_system,  # Usually CIEL or SNOMED
                        code=reaction['manifestation_code'],
                        display=reaction.get('manifestation_text', '')
                    )
                )

            fhir_reaction['manifestation'] = [
                CodeableConcept(
                    coding=manifestation_codings if manifestation_codings else None,
                    text=reaction.get('manifestation_text', 'Unknown reaction')
                )
            ]

            # Description
            if reaction.get('description'):
                fhir_reaction['description'] = reaction['description']

            # Severity
            if reaction.get('severity'):
                fhir_reaction['severity'] = reaction['severity']

            # Onset
            if reaction.get('onset'):
                fhir_reaction['onset'] = reaction['onset']

            fhir_reactions.append(fhir_reaction)

        fhir_allergy.reaction = fhir_reactions

    # Notes
    if allergy.note:
        fhir_allergy.note = [
            Annotation(text=allergy.note)
        ]

    return fhir_allergy
