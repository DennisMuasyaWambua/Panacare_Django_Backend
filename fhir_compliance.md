
# FHIR Compliance

This document describes the FHIR (Fast Healthcare Interoperability Resources) compliance features of the Panacare Healthcare Backend.

## Overview

The backend provides FHIR-compliant representations of key healthcare data. This allows for interoperability with other healthcare systems that support the FHIR standard.

## FHIR Resources

The following Django models are mapped to FHIR resources:

- **Patient:** Maps to the FHIR `Patient` resource.
- **Doctor:** Maps to the FHIR `Practitioner` resource.
- **HealthCare:** Maps to the FHIR `Organization` resource.
- **PatientDoctorAssignment:** Maps to the FHIR `Encounter` resource.

## Accessing FHIR Data

There are two ways to retrieve data in FHIR format:

### 1. Using the `format` Query Parameter

You can add the `format=fhir` query parameter to the regular API endpoints to get a FHIR-compliant response.

**Examples:**

```
GET /api/patients/?format=fhir
GET /api/doctors/456/?format=fhir
```

### 2. Dedicated FHIR Endpoints

The API provides dedicated endpoints under the `/fhir/` path that follow FHIR conventions.

**Endpoints:**

- `GET /fhir/Patient/`
- `GET /fhir/Patient/{id}/`
- `GET /fhir/Practitioner/`
- `GET /fhir/Practitioner/{id}/`
- `GET /fhir/Organization/`
- `GET /fhir/Organization/{id}/`
- `GET /fhir/Encounter/`
- `GET /fhir/Encounter/{id}/`

### Metadata

A FHIR CapabilityStatement is available at the following endpoint, which describes the server's capabilities:

```
GET /fhir/metadata
```

## FHIR Profiles and Mapping

The FHIR representations follow the US Core profiles. The mapping from the backend models to the FHIR resource fields is detailed below.

### Patient

| Model Field                  | FHIR Field                         |
| ---------------------------- | ---------------------------------- |
| id                           | `id`                               |
| user.first_name, user.last_name | `name`                             |
| user.email                   | `telecom` (email)                  |
| user.phone_number            | `telecom` (phone)                  |
| user.address                 | `address`                          |
| gender                       | `gender`                           |
| date_of_birth                | `birthDate`                        |
| ...                          | ...                                |

### Doctor (Practitioner)

| Model Field                  | FHIR Field                         |
| ---------------------------- | ---------------------------------- |
| id                           | `id`                               |
| user.first_name, user.last_name | `name`                             |
| specialty                    | `qualification.code`               |
| license_number               | `identifier`                       |
| ...                          | ...                                |

### HealthCare (Organization)

| Model Field                  | FHIR Field                         |
| ---------------------------- | ---------------------------------- |
| id                           | `id`                               |
| name                         | `name`                             |
| category                     | `type`                             |
| ...                          | ...                                |

### PatientDoctorAssignment (Encounter)

| Model Field                  | FHIR Field                         |
| ---------------------------- | ---------------------------------- |
| id                           | `id`                               |
| status                       | `status`                           |
| encounter_type               | `class`                            |
| patient                      | `subject`                          |
| doctor                       | `participant.individual`           |
| ...                          | ...                                |

*(Note: The tables above are a summary. For a complete list of field mappings, please refer to the project's internal documentation or the `to_fhir_json()` methods in the models.)*

## Content-Type Header

When requesting data in FHIR format, the `Content-Type` header of the response is set to `application/fhir+json`.
