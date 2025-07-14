# Panacare Healthcare API Endpoint Payloads

This document provides a comprehensive overview of all API endpoints in the Panacare Healthcare Backend, along with their expected JSON payloads.

## Table of Contents

1. [Users App](#users-app)
   - [Role Endpoints](#role-endpoints)
   - [User Registration/Authentication](#user-registrationauthentication)
   - [User Management](#user-management)
   - [Patient Endpoints](#patient-endpoints)
   - [Account Management](#account-management)
   - [Support](#support)

2. [Doctors App](#doctors-app)
   - [Doctor Management](#doctor-management)
   - [Ratings](#ratings)
   - [Admin Doctor Endpoints](#admin-doctor-endpoints)

3. [Healthcare App](#healthcare-app)
   - [Healthcare Facilities](#healthcare-facilities)
   - [Patient-Doctor Assignment](#patient-doctor-assignment)
   - [Doctor Availability](#doctor-availability)
   - [Appointments](#appointments)
   - [Appointment Documents](#appointment-documents)
   - [Consultations](#consultations)
   - [Packages and Subscriptions](#packages-and-subscriptions)
   - [Resources](#resources)
   - [Doctor Ratings](#doctor-ratings)

4. [Clinical Support App](#clinical-support-app)
   - [Clinical Decision Support](#clinical-decision-support)

5. [FHIR API](#fhir-api)
   - [FHIR Resources](#fhir-resources)

## Users App

### Role Endpoints

#### GET /api/roles/
List all roles

#### POST /api/roles/
Create a new role
```json
{
  "name": "string",
  "description": "string"
}
```

#### GET /api/roles/{id}/
Get role details

#### PUT /api/roles/{id}/
Update a role
```json
{
  "name": "string",
  "description": "string"
}
```

#### DELETE /api/roles/{id}/
Delete a role

### User Registration/Authentication

#### POST /api/users/register/
Register a new user
```json
{
  "email": "string",
  "password": "string",
  "first_name": "string",
  "last_name": "string",
  "phone_number": "string",
  "address": "string",
  "role": "string"
}
```

#### POST /api/users/login/
Login a user
```json
{
  "email": "string",
  "password": "string"
}
```

#### GET /api/users/activate/{uidb64}/{token}/
Activate a user account

#### POST /api/users/register-admin/
Register an admin user
```json
{
  "admin_token": "string",
  "email": "string",
  "password": "string",
  "first_name": "string",
  "last_name": "string",
  "phone_number": "string",
  "address": "string"
}
```

### User Management

#### GET /api/users/
List all users

#### GET /api/users/{id}/
Get user details

#### PUT /api/users/{id}/
Update a user
```json
{
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "phone_number": "string",
  "address": "string"
}
```

#### DELETE /api/users/{id}/
Delete a user

### Patient Endpoints

#### GET /api/patients/
List all patients

#### GET /api/patients/{id}/
Get patient details

#### GET /api/patient/profile/
Get current patient's profile

#### PUT /api/patient/profile/
Update current patient's profile
```json
{
  "date_of_birth": "YYYY-MM-DD",
  "gender": "male|female|other|unknown",
  "marital_status": "M|S|D|W|U",
  "language": "string",
  "blood_type": "A+|A-|B+|B-|AB+|AB-|O+|O-",
  "height_cm": "integer",
  "weight_kg": "decimal",
  "allergies": "string",
  "medical_conditions": "string",
  "medications": "string",
  "emergency_contact_name": "string",
  "emergency_contact_phone": "string",
  "emergency_contact_relationship": "string",
  "insurance_provider": "string",
  "insurance_policy_number": "string",
  "insurance_group_number": "string"
}
```

### Account Management

#### POST /api/users/resend-verification/
Resend verification email
```json
{
  "email": "string"
}
```

#### POST /api/users/change-password/
Change password
```json
{
  "current_password": "string",
  "new_password": "string"
}
```

#### POST /api/users/change-email/
Change email
```json
{
  "password": "string",
  "new_email": "string"
}
```

#### POST /api/users/change-phone/
Change phone number
```json
{
  "password": "string",
  "new_phone_number": "string"
}
```

#### POST /api/forgot-password/
Request password reset
```json
{
  "email": "string"
}
```

#### POST /api/reset-password/{uidb64}/{token}/
Reset password
```json
{
  "new_password": "string"
}
```

### Support

#### POST /api/contact-us/
Submit contact form
```json
{
  "name": "string",
  "email": "string",
  "subject": "string",
  "message": "string"
}
```

#### POST /api/support-request/
Submit support request
```json
{
  "subject": "string",
  "message": "string",
  "request_type": "technical|billing|account|feedback|other",
  "priority": "low|medium|high|urgent"
}
```

## Doctors App

### Doctor Management

#### GET /api/doctors/
List all doctors

Query Parameters:
- specialty
- available
- name
- location

#### GET /api/doctors/{id}/
Get doctor details

#### POST /api/doctors/
Create a doctor profile
```json
{
  "user_id": "uuid",
  "specialty": "string",
  "license_number": "string",
  "experience_years": "integer",
  "bio": "string",
  "education": "integer",
  "is_verified": "boolean",
  "is_available": "boolean",
  "communication_languages": "string"
}
```

#### POST /api/doctors/add_profile/
Add doctor profile
```json
{
  "specialty": "string",
  "license_number": "string",
  "experience_years": "integer",
  "bio": "string",
  "education": {
    "level_of_education": "string",
    "field": "string",
    "institution": "string",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD"
  },
  "is_available": "boolean",
  "communication_languages": "string"
}
```

#### GET /api/doctors/profile/
Get current doctor's profile

### Ratings

#### GET /api/doctors/{id}/ratings/
Get doctor ratings

#### GET /api/doctors/{id}/rating_summary/
Get doctor rating summary

#### POST /api/doctors/{id}/review/
Create a review for a doctor
```json
{
  "rating": "integer",
  "review": "string",
  "is_anonymous": "boolean"
}
```

### Admin Doctor Endpoints

#### POST /api/doctors/admin_add_doctor/
Admin: Add a new doctor
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "first_name": "string",
  "last_name": "string",
  "phone_number": "string",
  "address": "string",
  "specialty": "string",
  "license_number": "string",
  "experience_years": "integer",
  "bio": "string",
  "education": {
    "level_of_education": "string",
    "field": "string",
    "institution": "string",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD"
  },
  "is_available": "boolean"
}
```

#### GET /api/doctors/admin_list_doctors/
Admin: List all doctors

#### GET /api/doctors/admin_view_doctor/{id}/
Admin: View doctor details

#### GET /api/doctors/admin_list_patients/
Admin: List all patients

#### GET /api/doctors/admin_view_patient/{id}/
Admin: View patient details

## Healthcare App

### Healthcare Facilities

#### GET /api/healthcare/
List healthcare facilities

Query Parameters:
- category
- name
- active

#### GET /api/healthcare/{id}/
Get healthcare facility details

#### POST /api/healthcare/
Create healthcare facility
```json
{
  "name": "string",
  "description": "string",
  "category": "GENERAL|PEDIATRIC|MENTAL|DENTAL|VISION|OTHER",
  "address": "string",
  "phone_number": "string",
  "email": "string",
  "website": "string",
  "is_verified": "boolean",
  "is_active": "boolean",
  "doctor_ids": ["uuid"],
  "city": "string",
  "state": "string",
  "postal_code": "string",
  "country": "string"
}
```

### Patient-Doctor Assignment

#### POST /api/healthcare/assign_patient_to_doctor/
Assign patient to doctor
```json
{
  "patient_id": "uuid",
  "doctor_id": "uuid",
  "notes": "string"
}
```

#### GET /api/healthcare/list_patient_doctor_assignments/
List patient-doctor assignments

Query Parameters:
- doctor_id
- patient_id

#### GET /api/healthcare/view_assignment/{id}/
View assignment details

### Doctor Availability

#### GET /api/doctor-availability/
List doctor availabilities

Query Parameters:
- doctor_id
- available
- day
- date

#### POST /api/doctor-availability/
Create doctor availability
```json
{
  "doctor": "uuid",
  "day_of_week": "integer",
  "start_time": "time",
  "end_time": "time",
  "is_recurring": "boolean",
  "specific_date": "YYYY-MM-DD",
  "is_available": "boolean",
  "notes": "string"
}
```

#### GET /api/doctor-availability/my_availability/
Get current doctor's availability

### Appointments

#### GET /api/appointments/
List appointments

Query Parameters:
- doctor_id
- patient_id
- status
- date_from
- date_to
- type

#### POST /api/appointments/
Create appointment
```json
{
  "patient": "uuid",
  "doctor": "uuid",
  "appointment_date": "YYYY-MM-DD",
  "start_time": "time",
  "end_time": "time",
  "status": "string",
  "appointment_type": "string",
  "reason": "string",
  "healthcare_facility": "uuid"
}
```

#### GET /api/appointments/my_appointments/
Get current patient's appointments

#### GET /api/appointments/doctor_appointments/
Get current doctor's appointments

#### POST /api/appointments/{id}/cancel_appointment/
Cancel appointment

#### POST /api/appointments/{id}/update_consultation_details/
Update consultation details
```json
{
  "diagnosis": "string",
  "treatment": "string",
  "notes": "string",
  "risk_level": "string",
  "status": "string"
}
```

### Appointment Documents

#### GET /api/appointment-documents/
List appointment documents

Query Parameters:
- appointment_id
- type

#### POST /api/appointment-documents/
Create appointment document
```json
{
  "appointment": "uuid",
  "title": "string",
  "file": "file",
  "document_type": "string",
  "description": "string"
}
```

### Consultations

#### GET /api/consultations/
List consultations

Query Parameters:
- appointment_id
- status

#### POST /api/consultations/
Create consultation
```json
{
  "appointment": "uuid",
  "status": "string",
  "session_id": "string",
  "recording_url": "string"
}
```

#### POST /api/consultations/{id}/start_consultation/
Start consultation

#### POST /api/consultations/{id}/end_consultation/
End consultation

### Packages and Subscriptions

#### GET /api/packages/
List packages

#### POST /api/packages/
Create package
```json
{
  "name": "string",
  "description": "string",
  "price": "decimal",
  "duration_days": "integer",
  "consultation_count": "integer",
  "max_doctors": "integer",
  "priority_support": "boolean",
  "access_to_resources": "boolean",
  "is_active": "boolean"
}
```

#### GET /api/subscriptions/
List subscriptions

Query Parameters:
- patient_id
- package_id
- status

#### POST /api/subscriptions/
Create subscription
```json
{
  "patient": "uuid",
  "package": "uuid",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "status": "string",
  "payment_reference": "string",
  "payment_date": "YYYY-MM-DD"
}
```

#### GET /api/subscriptions/my_subscriptions/
Get current patient's subscriptions

#### POST /api/subscriptions/{id}/cancel_subscription/
Cancel subscription

### Resources

#### GET /api/resources/
List resources

Query Parameters:
- category
- content_type
- search

#### POST /api/resources/
Create resource
```json
{
  "title": "string",
  "description": "string",
  "content_type": "string",
  "file": "file",
  "url": "string",
  "text_content": "string",
  "is_password_protected": "boolean",
  "password_hash": "string",
  "category": "string",
  "tags": "string"
}
```

#### POST /api/resources/{id}/approve_resource/
Approve resource

#### POST /api/resources/{id}/verify_password/
Verify resource password
```json
{
  "password": "string"
}
```

### Doctor Ratings

#### GET /api/doctor-ratings/
List doctor ratings

Query Parameters:
- doctor_id
- patient_id
- rating

#### POST /api/doctor-ratings/
Create doctor rating
```json
{
  "doctor": "uuid",
  "rating": "integer",
  "review": "string",
  "is_anonymous": "boolean"
}
```

#### GET /api/doctor-ratings/doctor_average_rating/
Get doctor average rating

Query Parameters:
- doctor_id

## Clinical Support App

### Clinical Decision Support

#### POST /api/clinical-decision/
Get clinical decision support
```json
{
  "age": "integer",
  "gender": "male|female|other",
  "weight": "float",
  "height": "float",
  "high_blood_pressure": "boolean",
  "diabetes": "boolean",
  "on_medication": "boolean",
  "headache": "boolean",
  "dizziness": "boolean",
  "blurred_vision": "boolean",
  "palpitations": "boolean",
  "fatigue": "boolean",
  "chest_pain": "boolean",
  "frequent_thirst": "boolean",
  "loss_of_appetite": "boolean",
  "frequent_urination": "boolean",
  "other_symptoms": "string",
  "no_symptoms": "boolean",
  "systolic_pressure": "integer",
  "diastolic_pressure": "integer",
  "blood_sugar": "float",
  "heart_rate": "integer",
  "sleep_hours": "float",
  "exercise_minutes": "integer",
  "eats_unhealthy": "boolean",
  "smokes": "boolean",
  "consumes_alcohol": "boolean",
  "skips_medication": "boolean"
}
```

#### GET /api/clinical-history/
Get patient's clinical history

## FHIR API

### FHIR Resources

#### GET /fhir/metadata
Get FHIR server capability statement

#### GET /fhir/Patient/
List patients in FHIR format

#### GET /fhir/Patient/{id}/
Get patient in FHIR format

#### GET /fhir/Practitioner/
List doctors in FHIR format

#### GET /fhir/Practitioner/{id}/
Get doctor in FHIR format

#### GET /fhir/Organization/
List healthcare facilities in FHIR format

#### GET /fhir/Organization/{id}/
Get healthcare facility in FHIR format

#### GET /fhir/Encounter/
List patient-doctor assignments in FHIR format

#### GET /fhir/Encounter/{id}/
Get patient-doctor assignment in FHIR format