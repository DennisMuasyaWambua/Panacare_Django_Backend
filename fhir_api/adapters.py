from fhir.resources.patient import Patient as FHIRPatient
from fhir.resources.practitioner import Practitioner as FHIRPractitioner
from fhir.resources.organization import Organization as FHIROrganization
from fhir.resources.encounter import Encounter as FHIREncounter
from fhir.resources.schedule import Schedule as FHIRSchedule
from fhir.resources.appointment import Appointment as FHIRAppointment
from fhir.resources.documentreference import DocumentReference as FHIRDocumentReference
from fhir.resources.diagnosticreport import DiagnosticReport as FHIRDiagnosticReport
from fhir.resources.procedure import Procedure as FHIRProcedure
from fhir.resources.careplan import CarePlan as FHIRCarePlan
from fhir.resources.careteam import CareTeam as FHIRCareTeam
from fhir.resources.task import Task as FHIRTask
from fhir.resources.communication import Communication as FHIRCommunication
from fhir.resources.medication import Medication as FHIRMedication
from fhir.resources.coverage import Coverage as FHIRCoverage
from fhir.resources.claim import Claim as FHIRClaim
from fhir.resources.consent import Consent as FHIRConsent
from fhir.resources.provenance import Provenance as FHIRProvenance
from fhir.resources.immunization import Immunization as FHIRImmunization
from fhir.resources.familymemberhistory import FamilyMemberHistory as FHIRFamilyMemberHistory
from fhir.resources.questionnaireresponse import QuestionnaireResponse as FHIRQuestionnaireResponse
from fhir.resources.specimen import Specimen as FHIRSpecimen
from fhir.resources.location import Location as FHIRLocation
from fhir.resources.device import Device as FHIRDevice
from fhir.resources.servicerequest import ServiceRequest as FHIRServiceRequest
from fhir.resources.bundle import Bundle
from fhir.resources.humanname import HumanName
from fhir.resources.contactpoint import ContactPoint
from fhir.resources.address import Address
from fhir.resources.reference import Reference
from fhir.resources.identifier import Identifier
from fhir.resources.meta import Meta
from fhir.resources.coding import Coding
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.period import Period
from fhir.resources.annotation import Annotation
from fhir.resources.attachment import Attachment

from users.models import User, Patient, Location as DjangoLocation, CommunityHealthProvider
from doctors.models import Doctor, Education
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
import datetime
import uuid


def create_fhir_patient(patient):
    """Convert a Patient model to a FHIR Patient resource"""
    
    # Get user data
    user = patient.user
    
    # Create FHIR Patient
    fhir_patient = FHIRPatient()
    
    # Set ID
    fhir_patient.id = str(patient.id)
    
    # Set meta
    fhir_patient.meta = Meta(
        profile=["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"]
    )
    
    # Set identifiers
    identifiers = []
    
    # Patient ID identifier
    patient_identifier = Identifier(
        system=patient.identifier_system or "urn:panacare:patient",
        value=str(patient.id)
    )
    identifiers.append(patient_identifier)
    
    # Add insurance as an identifier if available
    if patient.insurance_policy_number:
        insurance_identifier = Identifier(
            system="urn:panacare:insurance",
            value=patient.insurance_policy_number,
            type=CodeableConcept(
                coding=[Coding(
                    system="http://terminology.hl7.org/CodeSystem/v2-0203",
                    code="PLAC",
                    display="Insurance Policy Number"
                )]
            )
        )
        identifiers.append(insurance_identifier)
    
    fhir_patient.identifier = identifiers
    
    # Set name
    human_name = HumanName(
        family=user.last_name,
        given=[user.first_name],
        use="official"
    )
    fhir_patient.name = [human_name]
    
    # Set contact (email and phone)
    contacts = []
    if user.email:
        email_contact = ContactPoint(
            system="email",
            value=user.email,
            use="home"
        )
        contacts.append(email_contact)
    
    if user.phone_number:
        phone_contact = ContactPoint(
            system="phone",
            value=user.phone_number,
            use="mobile"
        )
        contacts.append(phone_contact)
    
    if contacts:
        fhir_patient.telecom = contacts
    
    # Set address
    if user.address:
        patient_address = Address(
            line=[user.address],
            use="home"
        )
        fhir_patient.address = [patient_address]
    
    # Set gender if available
    if patient.gender:
        gender_map = {
            'male': 'male',
            'female': 'female',
            'other': 'other',
            'unknown': 'unknown'
        }
        fhir_patient.gender = gender_map.get(patient.gender, 'unknown')
    
    # Set birthDate if available
    if patient.date_of_birth:
        fhir_patient.birthDate = patient.date_of_birth.isoformat()
    
    # Set marital status if available
    if patient.marital_status:
        marital_status_map = {
            'M': 'M',  # Married
            'S': 'S',  # Single
            'D': 'D',  # Divorced
            'W': 'W',  # Widowed
            'U': 'UNK'  # Unknown
        }
        marital_code = marital_status_map.get(patient.marital_status, 'UNK')
        fhir_patient.maritalStatus = CodeableConcept(
            coding=[Coding(
                system="http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
                code=marital_code
            )]
        )
    
    # Set communication language if available
    if patient.language:
        fhir_patient.communication = [
            {
                "language": CodeableConcept(
                    coding=[Coding(
                        system="urn:ietf:bcp:47",
                        code=patient.language
                    )]
                ),
                "preferred": True
            }
        ]
    
    # Set active status
    fhir_patient.active = patient.active and user.is_active and user.is_verified
    
    # Set contact
    if patient.emergency_contact_name and patient.emergency_contact_phone:
        emergency_contact = {
            "relationship": [
                CodeableConcept(
                    text=patient.emergency_contact_relationship or "Emergency Contact"
                )
            ],
            "name": HumanName(
                text=patient.emergency_contact_name
            ),
            "telecom": [
                ContactPoint(
                    system="phone",
                    value=patient.emergency_contact_phone
                )
            ]
        }
        fhir_patient.contact = [emergency_contact]
    
    return fhir_patient


def create_fhir_practitioner(doctor):
    """Convert a Doctor model to a FHIR Practitioner resource"""
    
    # Get user data
    user = doctor.user
    
    # Create FHIR Practitioner
    fhir_practitioner = FHIRPractitioner()
    
    # Set ID
    fhir_practitioner.id = str(doctor.id)
    
    # Set meta
    fhir_practitioner.meta = Meta(
        profile=["http://hl7.org/fhir/us/core/StructureDefinition/us-core-practitioner"]
    )
    
    # Set identifiers
    identifiers = []
    
    # Doctor ID identifier
    doctor_identifier = Identifier(
        system="urn:panacare:practitioner",
        value=str(doctor.id)
    )
    identifiers.append(doctor_identifier)
    
    # License number as identifier
    if doctor.license_number:
        license_identifier = Identifier(
            system="urn:panacare:license",
            value=doctor.license_number,
            type=CodeableConcept(
                coding=[Coding(
                    system="http://terminology.hl7.org/CodeSystem/v2-0203",
                    code="MD",
                    display="Medical License number"
                )]
            )
        )
        identifiers.append(license_identifier)
    
    fhir_practitioner.identifier = identifiers
    
    # Set name
    human_name = HumanName(
        family=user.last_name,
        given=[user.first_name],
        use="official"
    )
    fhir_practitioner.name = [human_name]
    
    # Set contact (email and phone)
    contacts = []
    if user.email:
        email_contact = ContactPoint(
            system="email",
            value=user.email,
            use="work"
        )
        contacts.append(email_contact)
    
    if user.phone_number:
        phone_contact = ContactPoint(
            system="phone",
            value=user.phone_number,
            use="work"
        )
        contacts.append(phone_contact)
    
    if contacts:
        fhir_practitioner.telecom = contacts
    
    # Set address
    if user.address:
        practitioner_address = Address(
            line=[user.address],
            use="work"
        )
        fhir_practitioner.address = [practitioner_address]
    
    # Set qualification (specialty, education)
    qualifications = []
    
    # Add specialty as qualification
    if doctor.specialty:
        specialty_qualification = dict(
            code=CodeableConcept(
                coding=[Coding(
                    system="http://terminology.hl7.org/CodeSystem/v2-0360",
                    code=doctor.specialty.upper().replace(" ", "_"),
                    display=doctor.specialty
                )]
            )
        )
        qualifications.append(specialty_qualification)
    
    # Add education as qualification if available
    if doctor.education:
        education = doctor.education
        edu_qualification = dict(
            code=CodeableConcept(
                coding=[Coding(
                    system="http://terminology.hl7.org/CodeSystem/v2-0360",
                    code=education.level_of_education.upper().replace(" ", "_"),
                    display=education.level_of_education
                )]
            ),
            issuer=dict(
                display=education.institution
            )
        )
        qualifications.append(edu_qualification)
    
    if qualifications:
        fhir_practitioner.qualification = qualifications
    
    # Set active status
    fhir_practitioner.active = doctor.is_available and doctor.is_verified and user.is_active
    
    return fhir_practitioner


def create_fhir_organization(healthcare):
    """Convert a HealthCare model to a FHIR Organization resource"""
    
    # Create FHIR Organization
    fhir_organization = FHIROrganization()
    
    # Set ID
    fhir_organization.id = str(healthcare.id)
    
    # Set meta
    fhir_organization.meta = Meta(
        profile=["http://hl7.org/fhir/us/core/StructureDefinition/us-core-organization"]
    )
    
    # Set identifiers
    org_identifier = Identifier(
        system="urn:panacare:organization",
        value=str(healthcare.id)
    )
    fhir_organization.identifier = [org_identifier]
    
    # Set name
    fhir_organization.name = healthcare.name
    
    # Set type based on category
    if healthcare.category:
        org_type = CodeableConcept(
            coding=[Coding(
                system="http://terminology.hl7.org/CodeSystem/organization-type",
                code=healthcare.category.lower(),
                display=healthcare.get_category_display()
            )]
        )
        fhir_organization.type = [org_type]
    
    # Set telecom (email and phone)
    contacts = []
    if healthcare.email:
        email_contact = ContactPoint(
            system="email",
            value=healthcare.email,
            use="work"
        )
        contacts.append(email_contact)
    
    if healthcare.phone_number:
        phone_contact = ContactPoint(
            system="phone",
            value=healthcare.phone_number,
            use="work"
        )
        contacts.append(phone_contact)
    
    if healthcare.website:
        web_contact = ContactPoint(
            system="url",
            value=healthcare.website,
            use="work"
        )
        contacts.append(web_contact)
    
    if contacts:
        fhir_organization.telecom = contacts
    
    # Set address
    if healthcare.address:
        org_address = Address(
            line=[healthcare.address],
            use="work"
        )
        fhir_organization.address = [org_address]
    
    # Set active status
    fhir_organization.active = healthcare.is_active and healthcare.is_verified
    
    return fhir_organization


def create_fhir_appointment(appointment):
    """Convert an Appointment model to a FHIR Appointment resource"""

    # Create FHIR Appointment
    fhir_appointment = FHIRAppointment()

    # Set ID
    fhir_appointment.id = str(appointment.id)

    # Set meta
    fhir_appointment.meta = Meta(
        profile=["http://hl7.org/fhir/StructureDefinition/Appointment"]
    )

    # Set identifiers
    appointment_identifier = Identifier(
        system=appointment.identifier_system or "urn:panacare:appointment",
        value=str(appointment.id)
    )
    fhir_appointment.identifier = [appointment_identifier]

    # Set status
    fhir_appointment.status = appointment.status

    # Set appointment type
    if appointment.appointment_type:
        fhir_appointment.appointmentType = CodeableConcept(
            coding=[Coding(
                system="http://terminology.hl7.org/CodeSystem/v2-0276",
                code=appointment.appointment_type,
                display=dict(appointment._meta.get_field('appointment_type').choices).get(appointment.appointment_type, appointment.appointment_type)
            )]
        )

    # Set reason
    if appointment.reason:
        fhir_appointment.reasonCode = [
            CodeableConcept(text=appointment.reason)
        ]

    # Set start and end times
    start_datetime = datetime.datetime.combine(appointment.appointment_date, appointment.start_time)
    end_datetime = datetime.datetime.combine(appointment.appointment_date, appointment.end_time)
    fhir_appointment.start = start_datetime.isoformat()
    fhir_appointment.end = end_datetime.isoformat()

    # Set participants
    participants = []

    # Patient participant
    participants.append({
        "actor": Reference(
            reference=f"Patient/{appointment.patient.id}",
            display=appointment.patient.user.get_full_name() or appointment.patient.user.email
        ),
        "status": "accepted",
        "required": "required"
    })

    # Practitioner participant
    participants.append({
        "actor": Reference(
            reference=f"Practitioner/{appointment.doctor.id}",
            display=f"Dr. {appointment.doctor.user.get_full_name()}"
        ),
        "status": "accepted",
        "required": "required"
    })

    # Healthcare facility participant
    if appointment.healthcare_facility:
        participants.append({
            "actor": Reference(
                reference=f"Organization/{appointment.healthcare_facility.id}",
                display=appointment.healthcare_facility.name
            ),
            "status": "accepted"
        })

    fhir_appointment.participant = participants

    # Set notes
    if appointment.notes:
        fhir_appointment.comment = appointment.notes

    return fhir_appointment


def create_fhir_encounter(assignment, type_code="AMB"):
    """Convert a PatientDoctorAssignment to a FHIR Encounter resource
    Default encounter type is ambulatory (AMB)
    """

    # Create FHIR Encounter
    fhir_encounter = FHIREncounter()

    # Set ID
    fhir_encounter.id = str(assignment.id)

    # Set meta
    fhir_encounter.meta = Meta(
        profile=["http://hl7.org/fhir/us/core/StructureDefinition/us-core-encounter"]
    )

    # Set status
    fhir_encounter.status = assignment.status if assignment.status else ("in-progress" if assignment.is_active else "finished")

    # Set class
    fhir_encounter.class_fhir = Coding(
        system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
        code=assignment.encounter_type if assignment.encounter_type else type_code,
        display=assignment.get_encounter_type_display() if assignment.encounter_type else "Ambulatory"
    )

    # Set type
    fhir_encounter.type = [
        CodeableConcept(
            coding=[Coding(
                system="http://terminology.hl7.org/CodeSystem/encounter-type",
                code="FOLLOWUP",
                display="Follow-up visit"
            )]
        )
    ]

    # Set patient
    fhir_encounter.subject = Reference(
        reference=f"Patient/{assignment.patient.id}",
        display=assignment.patient.user.get_full_name() or assignment.patient.user.username
    )

    # Set practitioner participants
    fhir_encounter.participant = [
        {
            "individual": Reference(
                reference=f"Practitioner/{assignment.doctor.id}",
                display=assignment.doctor.user.get_full_name() or assignment.doctor.user.username
            ),
            "type": [
                CodeableConcept(
                    coding=[Coding(
                        system="http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                        code="PPRF",
                        display="Primary performer"
                    )]
                )
            ]
        }
    ]

    # Set period
    period_dict = {}
    if assignment.actual_start:
        period_dict["start"] = assignment.actual_start.isoformat()
    elif assignment.scheduled_start:
        period_dict["start"] = assignment.scheduled_start.isoformat()
    else:
        period_dict["start"] = assignment.created_at.isoformat()

    if assignment.actual_end:
        period_dict["end"] = assignment.actual_end.isoformat()
    elif not assignment.is_active:
        period_dict["end"] = assignment.updated_at.isoformat()

    if period_dict:
        fhir_encounter.period = period_dict

    # Set reason
    if assignment.reason or assignment.notes:
        fhir_encounter.reasonCode = [
            CodeableConcept(text=assignment.reason or assignment.notes)
        ]

    # Set service provider
    if assignment.healthcare_facility:
        fhir_encounter.serviceProvider = Reference(
            reference=f"Organization/{assignment.healthcare_facility.id}",
            display=assignment.healthcare_facility.name
        )

    return fhir_encounter


def create_fhir_service_request(referral):
    """Convert a Referral model to a FHIR ServiceRequest resource"""

    # Create FHIR ServiceRequest
    fhir_service_request = FHIRServiceRequest()

    # Set ID
    fhir_service_request.id = str(referral.id)

    # Set meta
    fhir_service_request.meta = Meta(
        profile=["http://hl7.org/fhir/StructureDefinition/ServiceRequest"]
    )

    # Set identifiers
    referral_identifier = Identifier(
        system="urn:panacare:referral",
        value=str(referral.id)
    )
    fhir_service_request.identifier = [referral_identifier]

    # Set status
    status_map = {
        'pending': 'active',
        'accepted': 'active',
        'declined': 'revoked',
        'completed': 'completed',
        'cancelled': 'revoked'
    }
    fhir_service_request.status = status_map.get(referral.status, 'active')

    # Set intent
    fhir_service_request.intent = "order"

    # Set priority
    fhir_service_request.priority = referral.urgency

    # Set subject (patient)
    fhir_service_request.subject = Reference(
        reference=f"Patient/{referral.patient.id}",
        display=referral.patient.user.get_full_name() or referral.patient.user.email
    )

    # Set requester (CHP)
    fhir_service_request.requester = Reference(
        reference=f"CommunityHealthProvider/{referral.referring_chp.id}",
        display=f"CHP: {referral.referring_chp.user.get_full_name()}"
    )

    # Set performer (doctor)
    fhir_service_request.performer = [
        Reference(
            reference=f"Practitioner/{referral.referred_to_doctor.id}",
            display=f"Dr. {referral.referred_to_doctor.user.get_full_name()}"
        )
    ]

    # Set reason
    if referral.referral_reason:
        fhir_service_request.reasonCode = [
            CodeableConcept(text=referral.referral_reason)
        ]

    # Set notes
    notes = []
    if referral.clinical_notes:
        notes.append(Annotation(text=referral.clinical_notes))
    if referral.doctor_notes:
        notes.append(Annotation(text=f"Doctor's notes: {referral.doctor_notes}"))
    if referral.follow_up_notes:
        notes.append(Annotation(text=f"Follow-up: {referral.follow_up_notes}"))

    if notes:
        fhir_service_request.note = notes

    # Set authored date
    fhir_service_request.authoredOn = referral.created_at.isoformat()

    return fhir_service_request


def create_fhir_document_reference(consultation):
    """Convert a Consultation to a FHIR DocumentReference resource for consultation notes"""

    # Create FHIR DocumentReference
    fhir_doc_ref = FHIRDocumentReference()

    # Set ID
    fhir_doc_ref.id = str(consultation.id)

    # Set meta
    fhir_doc_ref.meta = Meta(
        profile=["http://hl7.org/fhir/StructureDefinition/DocumentReference"]
    )

    # Set identifiers
    doc_identifier = Identifier(
        system="urn:panacare:consultation-document",
        value=str(consultation.id)
    )
    fhir_doc_ref.identifier = [doc_identifier]

    # Set status
    status_map = {
        'scheduled': 'current',
        'in-progress': 'current',
        'completed': 'current',
        'cancelled': 'entered-in-error',
        'missed': 'entered-in-error'
    }
    fhir_doc_ref.status = status_map.get(consultation.status, 'current')

    # Set docStatus
    if consultation.status == 'completed':
        fhir_doc_ref.docStatus = 'final'
    elif consultation.status in ['in-progress', 'scheduled']:
        fhir_doc_ref.docStatus = 'preliminary'

    # Set type (consultation note)
    fhir_doc_ref.type = CodeableConcept(
        coding=[Coding(
            system="http://loinc.org",
            code="11488-4",
            display="Consultation note"
        )]
    )

    # Set category
    fhir_doc_ref.category = [
        CodeableConcept(
            coding=[Coding(
                system="http://hl7.org/fhir/us/core/CodeSystem/us-core-documentreference-category",
                code="clinical-note",
                display="Clinical Note"
            )]
        )
    ]

    # Set subject (patient)
    fhir_doc_ref.subject = Reference(
        reference=f"Patient/{consultation.appointment.patient.id}",
        display=consultation.appointment.patient.user.get_full_name() or consultation.appointment.patient.user.email
    )

    # Set date
    fhir_doc_ref.date = consultation.start_time.isoformat() if consultation.start_time else consultation.created_at.isoformat()

    # Set author (practitioner)
    fhir_doc_ref.author = [
        Reference(
            reference=f"Practitioner/{consultation.appointment.doctor.id}",
            display=f"Dr. {consultation.appointment.doctor.user.get_full_name()}"
        )
    ]

    # Set context (encounter)
    fhir_doc_ref.context = {
        "encounter": [
            Reference(
                reference=f"Appointment/{consultation.appointment.id}",
                display=f"Appointment on {consultation.appointment.appointment_date}"
            )
        ],
        "period": {
            "start": consultation.start_time.isoformat() if consultation.start_time else consultation.created_at.isoformat(),
            "end": consultation.end_time.isoformat() if consultation.end_time else None
        }
    }

    # Set content
    content = []
    if consultation.recording_url:
        content.append({
            "attachment": Attachment(
                contentType="video/mp4",
                url=consultation.recording_url,
                title="Consultation Recording"
            ),
            "format": Coding(
                system="http://ihe.net/fhir/ValueSet/IHE.FormatCode.codesystem",
                code="urn:ihe:iti:xds:2017:mimeTypeSufficient",
                display="mimeType Sufficient"
            )
        })

    # Add consultation notes as text content
    notes_text = f"Consultation Status: {consultation.status}\n"
    if consultation.appointment.diagnosis:
        notes_text += f"Diagnosis: {consultation.appointment.diagnosis}\n"
    if consultation.appointment.treatment:
        notes_text += f"Treatment: {consultation.appointment.treatment}\n"
    if consultation.appointment.notes:
        notes_text += f"Notes: {consultation.appointment.notes}\n"

    content.append({
        "attachment": Attachment(
            contentType="text/plain",
            data=notes_text.encode('utf-8'),
            title="Consultation Notes"
        )
    })

    fhir_doc_ref.content = content

    return fhir_doc_ref


def create_fhir_care_plan(appointment):
    """Convert an Appointment with treatment plan to a FHIR CarePlan resource"""

    # Create FHIR CarePlan
    fhir_care_plan = FHIRCarePlan()

    # Set ID
    fhir_care_plan.id = f"careplan-{str(appointment.id)}"

    # Set meta
    fhir_care_plan.meta = Meta(
        profile=["http://hl7.org/fhir/StructureDefinition/CarePlan"]
    )

    # Set identifiers
    plan_identifier = Identifier(
        system="urn:panacare:careplan",
        value=f"careplan-{str(appointment.id)}"
    )
    fhir_care_plan.identifier = [plan_identifier]

    # Set status
    status_map = {
        'proposed': 'draft',
        'pending': 'draft',
        'booked': 'active',
        'arrived': 'active',
        'fulfilled': 'completed',
        'cancelled': 'revoked',
        'noshow': 'revoked',
        'scheduled': 'active'
    }
    fhir_care_plan.status = status_map.get(appointment.status, 'active')

    # Set intent
    fhir_care_plan.intent = "plan"

    # Set title
    fhir_care_plan.title = f"Care Plan from Appointment on {appointment.appointment_date}"

    # Set subject (patient)
    fhir_care_plan.subject = Reference(
        reference=f"Patient/{appointment.patient.id}",
        display=appointment.patient.user.get_full_name() or appointment.patient.user.email
    )

    # Set period
    start_datetime = datetime.datetime.combine(appointment.appointment_date, appointment.start_time)
    fhir_care_plan.period = {
        "start": start_datetime.isoformat()
    }

    # Set author (practitioner)
    fhir_care_plan.author = Reference(
        reference=f"Practitioner/{appointment.doctor.id}",
        display=f"Dr. {appointment.doctor.user.get_full_name()}"
    )

    # Set care team (if CHP created the appointment)
    if appointment.created_by_chp:
        fhir_care_plan.careTeam = [
            Reference(
                reference=f"CareTeam/team-{appointment.id}",
                display=f"Care team for {appointment.patient.user.get_full_name()}"
            )
        ]

    # Set activity (treatment)
    if appointment.treatment:
        fhir_care_plan.activity = [
            {
                "detail": {
                    "status": "completed" if appointment.status == 'fulfilled' else "in-progress",
                    "description": appointment.treatment
                }
            }
        ]

    # Set notes
    notes = []
    if appointment.diagnosis:
        notes.append(Annotation(text=f"Diagnosis: {appointment.diagnosis}"))
    if appointment.notes:
        notes.append(Annotation(text=appointment.notes))

    if notes:
        fhir_care_plan.note = notes

    return fhir_care_plan


def create_fhir_care_team(appointment):
    """Create a FHIR CareTeam resource from an appointment with CHP involvement"""

    # Create FHIR CareTeam
    fhir_care_team = FHIRCareTeam()

    # Set ID
    fhir_care_team.id = f"team-{str(appointment.id)}"

    # Set meta
    fhir_care_team.meta = Meta(
        profile=["http://hl7.org/fhir/StructureDefinition/CareTeam"]
    )

    # Set identifiers
    team_identifier = Identifier(
        system="urn:panacare:careteam",
        value=f"team-{str(appointment.id)}"
    )
    fhir_care_team.identifier = [team_identifier]

    # Set status
    status_map = {
        'proposed': 'proposed',
        'pending': 'proposed',
        'booked': 'active',
        'arrived': 'active',
        'fulfilled': 'inactive',
        'cancelled': 'inactive',
        'noshow': 'inactive',
        'scheduled': 'active'
    }
    fhir_care_team.status = status_map.get(appointment.status, 'active')

    # Set name
    fhir_care_team.name = f"Care Team for {appointment.patient.user.get_full_name()}"

    # Set subject (patient)
    fhir_care_team.subject = Reference(
        reference=f"Patient/{appointment.patient.id}",
        display=appointment.patient.user.get_full_name() or appointment.patient.user.email
    )

    # Set period
    start_datetime = datetime.datetime.combine(appointment.appointment_date, appointment.start_time)
    fhir_care_team.period = {
        "start": start_datetime.isoformat()
    }

    # Set participants
    participants = [
        {
            "role": [
                CodeableConcept(
                    coding=[Coding(
                        system="http://snomed.info/sct",
                        code="223366009",
                        display="Healthcare professional"
                    )]
                )
            ],
            "member": Reference(
                reference=f"Practitioner/{appointment.doctor.id}",
                display=f"Dr. {appointment.doctor.user.get_full_name()}"
            )
        }
    ]

    # Add CHP if present
    if appointment.created_by_chp:
        participants.append({
            "role": [
                CodeableConcept(
                    coding=[Coding(
                        system="http://snomed.info/sct",
                        code="768730001",
                        display="Community health worker"
                    )]
                )
            ],
            "member": Reference(
                reference=f"CommunityHealthProvider/{appointment.created_by_chp.id}",
                display=appointment.created_by_chp.user.get_full_name()
            )
        })

    fhir_care_team.participant = participants

    # Set managing organization
    if appointment.healthcare_facility:
        fhir_care_team.managingOrganization = [
            Reference(
                reference=f"Organization/{appointment.healthcare_facility.id}",
                display=appointment.healthcare_facility.name
            )
        ]

    return fhir_care_team


def create_fhir_task(referral):
    """Convert a Referral to a FHIR Task resource for workflow management"""

    # Create FHIR Task
    fhir_task = FHIRTask()

    # Set ID
    fhir_task.id = f"task-{str(referral.id)}"

    # Set meta
    fhir_task.meta = Meta(
        profile=["http://hl7.org/fhir/StructureDefinition/Task"]
    )

    # Set identifiers
    task_identifier = Identifier(
        system="urn:panacare:task",
        value=f"task-{str(referral.id)}"
    )
    fhir_task.identifier = [task_identifier]

    # Set status
    status_map = {
        'pending': 'requested',
        'accepted': 'accepted',
        'declined': 'rejected',
        'completed': 'completed',
        'cancelled': 'cancelled'
    }
    fhir_task.status = status_map.get(referral.status, 'requested')

    # Set intent
    fhir_task.intent = "order"

    # Set priority
    fhir_task.priority = referral.urgency

    # Set code (referral task)
    fhir_task.code = CodeableConcept(
        coding=[Coding(
            system="http://hl7.org/fhir/CodeSystem/task-code",
            code="fulfill",
            display="Fulfill the focal request"
        )]
    )

    # Set description
    fhir_task.description = f"Review and accept referral: {referral.referral_reason}"

    # Set focus (the referral ServiceRequest)
    fhir_task.focus = Reference(
        reference=f"ServiceRequest/{referral.id}",
        display="Referral request"
    )

    # Set for (patient)
    fhir_task.for_fhir = Reference(
        reference=f"Patient/{referral.patient.id}",
        display=referral.patient.user.get_full_name() or referral.patient.user.email
    )

    # Set requester (CHP)
    fhir_task.requester = Reference(
        reference=f"CommunityHealthProvider/{referral.referring_chp.id}",
        display=f"CHP: {referral.referring_chp.user.get_full_name()}"
    )

    # Set owner (doctor)
    fhir_task.owner = Reference(
        reference=f"Practitioner/{referral.referred_to_doctor.id}",
        display=f"Dr. {referral.referred_to_doctor.user.get_full_name()}"
    )

    # Set authored date
    fhir_task.authoredOn = referral.created_at.isoformat()

    # Set last modified
    fhir_task.lastModified = referral.updated_at.isoformat()

    # Set notes
    notes = []
    if referral.clinical_notes:
        notes.append(Annotation(
            text=referral.clinical_notes,
            time=referral.created_at.isoformat()
        ))
    if referral.doctor_notes:
        notes.append(Annotation(
            text=referral.doctor_notes,
            time=referral.updated_at.isoformat()
        ))

    if notes:
        fhir_task.note = notes

    return fhir_task


def create_fhir_communication(chat_message):
    """Convert a ConsultationChat message to a FHIR Communication resource"""

    # Create FHIR Communication
    fhir_communication = FHIRCommunication()

    # Set ID
    fhir_communication.id = str(chat_message.id)

    # Set meta
    fhir_communication.meta = Meta(
        profile=["http://hl7.org/fhir/StructureDefinition/Communication"]
    )

    # Set identifiers
    comm_identifier = Identifier(
        system="urn:panacare:communication",
        value=str(chat_message.id)
    )
    fhir_communication.identifier = [comm_identifier]

    # Set status
    fhir_communication.status = "completed"

    # Set category
    fhir_communication.category = [
        CodeableConcept(
            coding=[Coding(
                system="http://terminology.hl7.org/CodeSystem/communication-category",
                code="notification",
                display="Notification"
            )]
        )
    ]

    # Set subject (patient)
    fhir_communication.subject = Reference(
        reference=f"Patient/{chat_message.consultation.appointment.patient.id}",
        display=chat_message.consultation.appointment.patient.user.get_full_name()
    )

    # Set encounter
    fhir_communication.encounter = Reference(
        reference=f"Appointment/{chat_message.consultation.appointment.id}",
        display=f"Consultation on {chat_message.consultation.appointment.appointment_date}"
    )

    # Set sent time
    fhir_communication.sent = chat_message.created_at.isoformat()

    # Set sender
    if chat_message.is_doctor:
        sender_ref = Reference(
            reference=f"Practitioner/{chat_message.consultation.appointment.doctor.id}",
            display=f"Dr. {chat_message.sender.get_full_name()}"
        )
    else:
        sender_ref = Reference(
            reference=f"Patient/{chat_message.consultation.appointment.patient.id}",
            display=chat_message.sender.get_full_name()
        )
    fhir_communication.sender = sender_ref

    # Set recipient
    if chat_message.is_doctor:
        recipient_ref = Reference(
            reference=f"Patient/{chat_message.consultation.appointment.patient.id}",
            display=chat_message.consultation.appointment.patient.user.get_full_name()
        )
    else:
        recipient_ref = Reference(
            reference=f"Practitioner/{chat_message.consultation.appointment.doctor.id}",
            display=f"Dr. {chat_message.consultation.appointment.doctor.user.get_full_name()}"
        )
    fhir_communication.recipient = [recipient_ref]

    # Set payload (message content)
    fhir_communication.payload = [
        {
            "contentString": chat_message.message
        }
    ]

    return fhir_communication


def create_fhir_coverage(subscription):
    """Convert a PatientSubscription to a FHIR Coverage resource"""

    # Create FHIR Coverage
    fhir_coverage = FHIRCoverage()

    # Set ID
    fhir_coverage.id = str(subscription.id)

    # Set meta
    fhir_coverage.meta = Meta(
        profile=["http://hl7.org/fhir/StructureDefinition/Coverage"]
    )

    # Set identifiers
    coverage_identifier = Identifier(
        system="urn:panacare:subscription",
        value=str(subscription.id)
    )
    fhir_coverage.identifier = [coverage_identifier]

    # Set status
    status_map = {
        'active': 'active',
        'expired': 'cancelled',
        'cancelled': 'cancelled',
        'pending': 'draft'
    }
    fhir_coverage.status = status_map.get(subscription.status, 'active')

    # Set type (subscription/insurance)
    fhir_coverage.type = CodeableConcept(
        coding=[Coding(
            system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
            code="EHCPOL",
            display="Extended healthcare"
        )],
        text="Subscription Plan"
    )

    # Set subscriber (patient)
    fhir_coverage.subscriber = Reference(
        reference=f"Patient/{subscription.patient.id}",
        display=subscription.patient.user.get_full_name() or subscription.patient.user.email
    )

    # Set beneficiary (patient)
    fhir_coverage.beneficiary = Reference(
        reference=f"Patient/{subscription.patient.id}",
        display=subscription.patient.user.get_full_name() or subscription.patient.user.email
    )

    # Set relationship (self)
    fhir_coverage.relationship = CodeableConcept(
        coding=[Coding(
            system="http://terminology.hl7.org/CodeSystem/subscriber-relationship",
            code="self",
            display="Self"
        )]
    )

    # Set period
    fhir_coverage.period = {
        "start": subscription.start_date.isoformat(),
        "end": subscription.end_date.isoformat()
    }

    # Set payor (organization - Panacare)
    fhir_coverage.payor = [
        Reference(
            display="Panacare Healthcare"
        )
    ]

    # Set class (plan details)
    fhir_coverage.class_fhir = [
        {
            "type": CodeableConcept(
                coding=[Coding(
                    system="http://terminology.hl7.org/CodeSystem/coverage-class",
                    code="plan",
                    display="Plan"
                )]
            ),
            "value": subscription.package.name,
            "name": subscription.package.name
        }
    ]

    # Set cost to beneficiary
    fhir_coverage.costToBeneficiary = [
        {
            "type": CodeableConcept(
                coding=[Coding(
                    system="http://terminology.hl7.org/CodeSystem/coverage-copay-type",
                    code="gpvisit",
                    display="General Practitioner Visit"
                )]
            ),
            "valueMoney": {
                "value": float(subscription.package.price),
                "currency": "KES"
            }
        }
    ]

    return fhir_coverage


def create_fhir_claim(payment, subscription):
    """Convert a Payment to a FHIR Claim resource"""

    # Create FHIR Claim
    fhir_claim = FHIRClaim()

    # Set ID
    fhir_claim.id = str(payment.id)

    # Set meta
    fhir_claim.meta = Meta(
        profile=["http://hl7.org/fhir/StructureDefinition/Claim"]
    )

    # Set identifiers
    claim_identifier = Identifier(
        system="urn:panacare:payment",
        value=payment.reference
    )
    fhir_claim.identifier = [claim_identifier]

    # Set status
    status_map = {
        'pending': 'active',
        'processing': 'active',
        'completed': 'active',
        'failed': 'cancelled',
        'cancelled': 'cancelled',
        'refunded': 'cancelled'
    }
    fhir_claim.status = status_map.get(payment.status, 'active')

    # Set type (institutional)
    fhir_claim.type = CodeableConcept(
        coding=[Coding(
            system="http://terminology.hl7.org/CodeSystem/claim-type",
            code="institutional",
            display="Institutional"
        )]
    )

    # Set use
    fhir_claim.use = "claim"

    # Set patient
    fhir_claim.patient = Reference(
        reference=f"Patient/{subscription.patient.id}",
        display=subscription.patient.user.get_full_name() or subscription.patient.user.email
    )

    # Set created
    fhir_claim.created = payment.created_at.isoformat()

    # Set provider (organization)
    fhir_claim.provider = Reference(
        display="Panacare Healthcare"
    )

    # Set priority
    fhir_claim.priority = CodeableConcept(
        coding=[Coding(
            system="http://terminology.hl7.org/CodeSystem/processpriority",
            code="normal",
            display="Normal"
        )]
    )

    # Set insurance
    fhir_claim.insurance = [
        {
            "sequence": 1,
            "focal": True,
            "coverage": Reference(
                reference=f"Coverage/{subscription.id}",
                display=f"Subscription: {subscription.package.name}"
            )
        }
    ]

    # Set item (subscription package)
    fhir_claim.item = [
        {
            "sequence": 1,
            "productOrService": CodeableConcept(
                text=subscription.package.name
            ),
            "unitPrice": {
                "value": float(payment.amount),
                "currency": payment.currency
            },
            "net": {
                "value": float(payment.amount),
                "currency": payment.currency
            }
        }
    ]

    # Set total
    fhir_claim.total = {
        "value": float(payment.amount),
        "currency": payment.currency
    }

    return fhir_claim


def create_fhir_consent(patient):
    """Create a FHIR Consent resource for telemedicine consent"""

    # Create FHIR Consent
    fhir_consent = FHIRConsent()

    # Set ID
    fhir_consent.id = f"consent-{str(patient.id)}"

    # Set meta
    fhir_consent.meta = Meta(
        profile=["http://hl7.org/fhir/StructureDefinition/Consent"]
    )

    # Set identifiers
    consent_identifier = Identifier(
        system="urn:panacare:consent",
        value=f"consent-{str(patient.id)}"
    )
    fhir_consent.identifier = [consent_identifier]

    # Set status (assuming active if patient is verified)
    fhir_consent.status = "active" if patient.user.is_verified else "proposed"

    # Set scope (patient privacy)
    fhir_consent.scope = CodeableConcept(
        coding=[Coding(
            system="http://terminology.hl7.org/CodeSystem/consentscope",
            code="patient-privacy",
            display="Privacy Consent"
        )]
    )

    # Set category (consent for treatment)
    fhir_consent.category = [
        CodeableConcept(
            coding=[Coding(
                system="http://loinc.org",
                code="59284-0",
                display="Consent Document"
            )]
        )
    ]

    # Set patient
    fhir_consent.patient = Reference(
        reference=f"Patient/{patient.id}",
        display=patient.user.get_full_name() or patient.user.email
    )

    # Set dateTime
    fhir_consent.dateTime = patient.created_at.isoformat()

    # Set policy (telemedicine consent)
    fhir_consent.policy = [
        {
            "uri": "https://panacare.health/policies/telemedicine-consent"
        }
    ]

    # Set provision (permit)
    fhir_consent.provision = {
        "type": "permit",
        "purpose": [
            Coding(
                system="http://terminology.hl7.org/CodeSystem/v3-ActReason",
                code="TREAT",
                display="Treatment"
            )
        ]
    }

    return fhir_consent


def create_fhir_provenance(resource_type, resource_id, created_by, created_at, updated_at=None):
    """Create a FHIR Provenance resource for audit trail"""

    # Create FHIR Provenance
    fhir_provenance = FHIRProvenance()

    # Set ID
    fhir_provenance.id = f"provenance-{resource_type}-{resource_id}"

    # Set meta
    fhir_provenance.meta = Meta(
        profile=["http://hl7.org/fhir/StructureDefinition/Provenance"]
    )

    # Set target (the resource being tracked)
    fhir_provenance.target = [
        Reference(
            reference=f"{resource_type}/{resource_id}"
        )
    ]

    # Set occurred (when the activity occurred)
    fhir_provenance.occurredDateTime = created_at.isoformat()

    # Set recorded (when it was recorded)
    fhir_provenance.recorded = updated_at.isoformat() if updated_at else created_at.isoformat()

    # Set activity (creation)
    fhir_provenance.activity = CodeableConcept(
        coding=[Coding(
            system="http://terminology.hl7.org/CodeSystem/v3-DataOperation",
            code="CREATE" if not updated_at else "UPDATE",
            display="create" if not updated_at else "revise or update"
        )]
    )

    # Set agent (who performed the action)
    agent_reference = None
    if hasattr(created_by, 'patient'):
        agent_reference = f"Patient/{created_by.patient.id}"
    elif hasattr(created_by, 'doctor'):
        agent_reference = f"Practitioner/{created_by.doctor.id}"
    elif hasattr(created_by, 'communityhealthprovider'):
        agent_reference = f"CommunityHealthProvider/{created_by.communityhealthprovider.id}"
    else:
        agent_reference = f"User/{created_by.id}"

    fhir_provenance.agent = [
        {
            "type": CodeableConcept(
                coding=[Coding(
                    system="http://terminology.hl7.org/CodeSystem/provenance-participant-type",
                    code="author",
                    display="Author"
                )]
            ),
            "who": Reference(
                reference=agent_reference,
                display=created_by.get_full_name() or created_by.email
            )
        }
    ]

    return fhir_provenance


def create_fhir_location(location):
    """Convert a Django Location model to a FHIR Location resource"""

    # Create FHIR Location
    fhir_location = FHIRLocation()

    # Set ID
    fhir_location.id = str(location.id)

    # Set meta
    fhir_location.meta = Meta(
        profile=["http://hl7.org/fhir/StructureDefinition/Location"]
    )

    # Set identifiers
    location_identifier = Identifier(
        system="urn:panacare:location",
        value=str(location.id)
    )
    fhir_location.identifier = [location_identifier]

    # Set status
    fhir_location.status = "active"

    # Set name
    fhir_location.name = location.name

    # Set mode
    fhir_location.mode = "instance"

    # Set type (based on level)
    type_map = {
        'county': 'COUNTRY',
        'sub_county': 'REGION',
        'ward': 'AREA',
        'village': 'VI'
    }

    fhir_location.type = [
        CodeableConcept(
            coding=[Coding(
                system="http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                code=type_map.get(location.level, 'AREA'),
                display=location.get_level_display()
            )]
        )
    ]

    # Set partOf (parent location)
    if location.parent:
        fhir_location.partOf = Reference(
            reference=f"Location/{location.parent.id}",
            display=location.parent.name
        )

    return fhir_location