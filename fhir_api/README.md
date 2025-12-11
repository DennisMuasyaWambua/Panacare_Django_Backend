# FHIR API for Panacare Healthcare Backend

This module provides FHIR (Fast Healthcare Interoperability Resources) compliant endpoints for the Panacare Healthcare Backend. It implements the FHIR R4 (4.0.1) standard.

## Available Resources

The following FHIR resources are currently implemented:

1. **Patient** - Mapped from Customer model
2. **Practitioner** - Mapped from Doctor model
3. **Organization** - Mapped from HealthCare model
4. **Encounter** - Mapped from PatientDoctorAssignment model

## Endpoints

All FHIR endpoints are accessible under the `/fhir/` prefix:

- `/fhir/metadata` - FHIR capability statement (publicly accessible)
- `/fhir/Patient/` - List all patients as FHIR Patient resources
- `/fhir/Patient/{id}/` - Get a specific patient as a FHIR Patient resource
- `/fhir/Practitioner/` - List all doctors as FHIR Practitioner resources
- `/fhir/Practitioner/{id}/` - Get a specific doctor as a FHIR Practitioner resource
- `/fhir/Organization/` - List all healthcare facilities as FHIR Organization resources
- `/fhir/Organization/{id}/` - Get a specific healthcare facility as a FHIR Organization resource
- `/fhir/Encounter/` - List all patient-doctor assignments as FHIR Encounter resources
- `/fhir/Encounter/{id}/` - Get a specific patient-doctor assignment as a FHIR Encounter resource

## Authentication

All endpoints except `/fhir/metadata` require authentication using JWT tokens. Include the token in the Authorization header:

```
Authorization: Bearer <your_token>
```

## Resource Mapping

### Customer → Patient

| Customer Model Field | FHIR Patient Field |
|---------------------|-------------------|
| id | id |
| user.first_name, user.last_name | name |
| user.email | telecom (email) |
| user.phone_number | telecom (phone) |
| user.address | address |
| gender | gender |
| date_of_birth | birthDate |
| user.is_active & user.is_verified | active |

### Doctor → Practitioner

| Doctor Model Field | FHIR Practitioner Field |
|---------------------|------------------------|
| id | id |
| user.first_name, user.last_name | name |
| user.email | telecom (email) |
| user.phone_number | telecom (phone) |
| user.address | address |
| specialty | qualification.code |
| education | qualification.code, qualification.issuer |
| license_number | identifier |
| is_available & is_verified & user.is_active | active |

### HealthCare → Organization

| HealthCare Model Field | FHIR Organization Field |
|------------------------|------------------------|
| id | id |
| name | name |
| category | type |
| email | telecom (email) |
| phone_number | telecom (phone) |
| website | telecom (url) |
| address | address |
| is_active & is_verified | active |

### PatientDoctorAssignment → Encounter

| PatientDoctorAssignment Model Field | FHIR Encounter Field |
|-------------------------------------|---------------------|
| id | id |
| is_active | status |
| patient | subject |
| doctor | participant.individual |
| created_at | period.start |
| updated_at | period.end |
| notes | reasonCode.text |

## Bundle Support

List endpoints return results as FHIR Bundle resources, containing multiple resources of the same type. The bundle type is "searchset" by default.

## Additional Notes

1. This implementation follows the US Core Implementation Guide where applicable.
2. All resources include identifiers with appropriate systems.
3. The implementation is read-only for now. Write operations (create, update, delete) will be added in future versions.