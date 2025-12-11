# FHIR Compliance in Panacare Healthcare Backend

This document describes how the Panacare Healthcare Backend has been made FHIR-compliant. FHIR (Fast Healthcare Interoperability Resources) is a standard for healthcare data exchange.

## FHIR Overview

FHIR is a standard developed by HL7 that enables healthcare information to be shared across systems. The standard defines a set of "Resources" that represent clinical concepts.

## FHIR Resources in Panacare

The following Django models have been made FHIR-compliant:

1. **Patient** - The Patient model represents a patient in FHIR terminology.
2. **Doctor → Practitioner** - The Doctor model represents a practitioner in FHIR.
3. **HealthCare → Organization** - The HealthCare facility model maps to an organization in FHIR.
4. **PatientDoctorAssignment → Encounter** - The assignment between a patient and doctor is represented as an encounter in FHIR.

## Accessing FHIR Data

There are two ways to access FHIR-compliant data:

### 1. Using format parameter with regular API endpoints

To access data in FHIR format, use the `format=fhir` query parameter with any API endpoint:

```
GET /api/patients/?format=fhir
GET /api/patients/123/?format=fhir
GET /api/doctors/?format=fhir
GET /api/doctors/456/?format=fhir
GET /api/healthcare/?format=fhir
GET /api/healthcare/789/?format=fhir
```

### 2. Using dedicated FHIR endpoints

Dedicated FHIR endpoints that follow FHIR naming conventions:

```
GET /fhir/Patient/
GET /fhir/Patient/123/
GET /fhir/Practitioner/
GET /fhir/Practitioner/456/
GET /fhir/Organization/
GET /fhir/Organization/789/
GET /fhir/Encounter/
GET /fhir/Encounter/101/
```

Additionally, a FHIR metadata endpoint is available that describes the server's capabilities:

```
GET /fhir/metadata
```

## FHIR Compliance Details

Each model includes a `to_fhir_json()` method that provides a FHIR-compliant JSON representation following these profiles:

- Patient: http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient
- Practitioner: http://hl7.org/fhir/us/core/StructureDefinition/us-core-practitioner
- Organization: http://hl7.org/fhir/us/core/StructureDefinition/us-core-organization
- Encounter: http://hl7.org/fhir/us/core/StructureDefinition/us-core-encounter

## Model Fields and FHIR Mapping

### Patient

| Model Field | FHIR Field |
|-------------|------------|
| id | id |
| user.first_name, user.last_name | name |
| user.email | telecom (email) |
| user.phone_number | telecom (phone) |
| user.address | address |
| gender | gender |
| date_of_birth | birthDate |
| active | active |
| marital_status | maritalStatus |
| language | communication.language |
| blood_type | extension (blood-type) |
| height_cm | extension (height) |
| weight_kg | extension (weight) |
| allergies | extension (allergies) |
| medical_conditions | extension (conditions) |
| medications | extension (medications) |
| emergency_contact_name | contact.name |
| emergency_contact_phone | contact.telecom |
| emergency_contact_relationship | contact.relationship |
| insurance_provider | extension (insurance) |
| insurance_policy_number | identifier (insurance) |
| insurance_group_number | extension (insurance-group) |
| identifier_system | identifier.system |

### Doctor (Practitioner)

| Model Field | FHIR Field |
|-------------|------------|
| id | id |
| user.first_name, user.last_name | name |
| user.email | telecom (email) |
| user.phone_number | telecom (phone) |
| user.address | address |
| specialty | qualification.code |
| education | qualification |
| license_number | identifier |
| is_available & is_verified & user.is_active | active |
| communication_languages | communication |
| identifier_system | identifier.system |
| license_system | identifier.system (for license number) |

### HealthCare (Organization)

| Model Field | FHIR Field |
|-------------|------------|
| id | id |
| name | name |
| category | type |
| email | telecom (email) |
| phone_number | telecom (phone) |
| website | telecom (url) |
| address | address.line |
| city | address.city |
| state | address.state |
| postal_code | address.postalCode |
| country | address.country |
| is_active & is_verified | active |
| part_of | partOf |
| identifier_system | identifier.system |

### PatientDoctorAssignment (Encounter)

| Model Field | FHIR Field |
|-------------|------------|
| id | id |
| status | status |
| encounter_type | class |
| patient | subject |
| doctor | participant.individual |
| reason, notes | reasonCode.text |
| healthcare_facility | serviceProvider |
| is_active | (contributes to status) |
| scheduled_start | period.start |
| scheduled_end | period.end |
| actual_start | period.start |
| actual_end | period.end |
| identifier_system | identifier.system |

## Headers

When data is returned in FHIR format, the Content-Type header is set to `application/fhir+json` in accordance with FHIR specifications.