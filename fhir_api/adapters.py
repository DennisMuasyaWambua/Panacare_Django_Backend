from fhir.resources.patient import Patient as FHIRPatient
from fhir.resources.practitioner import Practitioner as FHIRPractitioner
from fhir.resources.organization import Organization as FHIROrganization
from fhir.resources.encounter import Encounter as FHIREncounter
from fhir.resources.schedule import Schedule as FHIRSchedule
from fhir.resources.appointment import Appointment as FHIRAppointment
from fhir.resources.bundle import Bundle
from fhir.resources.humanname import HumanName
from fhir.resources.contactpoint import ContactPoint
from fhir.resources.address import Address
from fhir.resources.reference import Reference
from fhir.resources.identifier import Identifier
from fhir.resources.meta import Meta
from fhir.resources.coding import Coding
from fhir.resources.codeableconcept import CodeableConcept

from users.models import User, Patient
from doctors.models import Doctor, Education
from healthcare.models import HealthCare, PatientDoctorAssignment
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
    
    # Set status (finished, in-progress, etc.)
    fhir_encounter.status = "finished" if not assignment.is_active else "in-progress"
    
    # Set class (inpatient, outpatient, etc.)
    fhir_encounter.class_fhir = Coding(
        system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
        code=type_code,
        display="Ambulatory" if type_code == "AMB" else "Virtual"
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
    
    # Set practitioner
    fhir_encounter.participant = [
        {
            "individual": Reference(
                reference=f"Practitioner/{assignment.doctor.id}",
                display=assignment.doctor.user.get_full_name() or assignment.doctor.user.username
            )
        }
    ]
    
    # Set date
    fhir_encounter.period = {
        "start": assignment.created_at.isoformat(),
        "end": assignment.updated_at.isoformat() if not assignment.is_active else None
    }
    
    # Set notes
    if assignment.notes:
        fhir_encounter.reasonCode = [
            CodeableConcept(
                text=assignment.notes
            )
        ]
    
    return fhir_encounter