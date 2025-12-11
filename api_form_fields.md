# Panacare Healthcare API Documentation: Form Fields

This document contains all form fields for the APIs in this codebase, organized by app and endpoint.

## Users App

### Roles

#### GET `/api/roles/`
- Method: GET
- Description: List all roles
- No form fields required

#### POST `/api/roles/`
- Method: POST
- Description: Create a new role (admin only)
- Required fields:
  - `name` (string): Role name
- Optional fields:
  - `description` (string): Role description

#### GET `/api/roles/{uuid}/`
- Method: GET
- Description: Get role details
- No form fields required

#### PUT `/api/roles/{uuid}/`
- Method: PUT
- Description: Update a role (admin only)
- Required fields:
  - `name` (string): Role name
- Optional fields:
  - `description` (string): Role description

#### DELETE `/api/roles/{uuid}/`
- Method: DELETE
- Description: Delete a role (admin only)
- No form fields required

### Users

#### GET `/api/users/`
- Method: GET
- Description: List all users (admin only)
- No form fields required

#### POST `/api/users/`
- Method: POST
- Description: Create a new user (admin only)
- Required fields:
  - `username` (string): Username
  - `email` (string): Email address
  - `password` (string): Password
- Optional fields:
  - `first_name` (string): First name
  - `last_name` (string): Last name
  - `phone_number` (string): Phone number
  - `address` (string): Address
  - `role_names` (list): List of role names

#### GET `/api/users/{uuid}/`
- Method: GET
- Description: Get user details
- No form fields required

#### PUT `/api/users/{uuid}/`
- Method: PUT
- Description: Update a user
- Fields same as POST

#### DELETE `/api/users/{uuid}/`
- Method: DELETE
- Description: Delete a user
- No form fields required

#### POST `/api/users/register/`
- Method: POST
- Description: Register a new user
- Required fields:
  - `username` (string): Username
  - `email` (string): Email address
  - `password` (string): Password
- Optional fields:
  - `first_name` (string): First name
  - `last_name` (string): Last name
  - `phone_number` (string): Phone number
  - `address` (string): Address
  - `role_names` (list): List of role names ['doctor', 'patient']

#### POST `/api/users/login/`
- Method: POST
- Description: Login
- Required fields:
  - `email` (string): Email address
  - `password` (string): Password

#### GET `/api/users/activate/{uidb64}/{token}/`
- Method: GET
- Description: Activate a user account
- No form fields required (parameters in URL)

#### POST `/api/users/register-admin/`
- Method: POST
- Description: Register an admin user
- Required fields:
  - `username` (string): Username
  - `email` (string): Email address
  - `password` (string): Password
  - `security_token` (string): Admin registration token
- Optional fields:
  - `first_name` (string): First name
  - `last_name` (string): Last name
  - `phone_number` (string): Phone number
  - `address` (string): Address

### Patients

#### GET `/api/patients/`
- Method: GET
- Description: List all patients (admin only)
- No form fields required
- Optional query parameters:
  - `format` (string): Set to 'fhir' to get FHIR-compliant response

#### POST `/api/patients/`
- Method: POST
- Description: Create a new patient (admin only)
- Required fields:
  - `user_id` (uuid): User ID
- Optional fields:
  - `date_of_birth` (date): Date of birth
  - `gender` (string): Gender (choices: 'male', 'female', 'other', 'unknown')
  - `active` (boolean): Whether the patient record is active
  - `marital_status` (string): Marital status (choices: 'M' - Married, 'S' - Single, 'D' - Divorced, 'W' - Widowed, 'U' - Unknown)
  - `language` (string): Preferred language, default 'en'
  - `blood_type` (string): Blood type (choices: 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')
  - `height_cm` (integer): Height in centimeters
  - `weight_kg` (decimal): Weight in kilograms
  - `allergies` (string): Known allergies
  - `medical_conditions` (string): Pre-existing medical conditions
  - `medications` (string): Current medications
  - `emergency_contact_name` (string): Emergency contact name
  - `emergency_contact_phone` (string): Emergency contact phone number
  - `emergency_contact_relationship` (string): Relationship to emergency contact
  - `insurance_provider` (string): Insurance provider name
  - `insurance_policy_number` (string): Insurance policy number
  - `insurance_group_number` (string): Insurance group number
  - `identifier_system` (string): FHIR identifier system URI

#### GET `/api/patients/{uuid}/`
- Method: GET
- Description: Get patient details
- No form fields required
- Optional query parameters:
  - `format` (string): Set to 'fhir' to get FHIR-compliant response

#### PUT `/api/patients/{uuid}/`
- Method: PUT
- Description: Update a patient
- Required fields:
  - `user_id` (uuid): User ID
- Optional fields: (Same as POST)
  - `date_of_birth` (date): Date of birth
  - `gender` (string): Gender (choices: 'male', 'female', 'other', 'unknown')
  - `active` (boolean): Whether the patient record is active
  - `marital_status` (string): Marital status (choices: 'M' - Married, 'S' - Single, 'D' - Divorced, 'W' - Widowed, 'U' - Unknown)
  - `language` (string): Preferred language, default 'en'
  - `blood_type` (string): Blood type (choices: 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')
  - `height_cm` (integer): Height in centimeters
  - `weight_kg` (decimal): Weight in kilograms
  - `allergies` (string): Known allergies
  - `medical_conditions` (string): Pre-existing medical conditions
  - `medications` (string): Current medications
  - `emergency_contact_name` (string): Emergency contact name
  - `emergency_contact_phone` (string): Emergency contact phone number
  - `emergency_contact_relationship` (string): Relationship to emergency contact
  - `insurance_provider` (string): Insurance provider name
  - `insurance_policy_number` (string): Insurance policy number
  - `insurance_group_number` (string): Insurance group number
  - `identifier_system` (string): FHIR identifier system URI

#### DELETE `/api/patients/{uuid}/`
- Method: DELETE
- Description: Delete a patient
- No form fields required

## Doctors App

#### GET `/api/doctors/`
- Method: GET
- Description: List doctors
- Optional query parameters:
  - `specialty` (string): Filter by specialty
  - `available` (boolean): Filter by availability
  - `format` (string): Set to 'fhir' to get FHIR-compliant response

#### POST `/api/doctors/`
- Method: POST
- Description: Create a doctor profile
- Required fields:
  - `user_id` (uuid): User ID
  - `specialty` (string): Medical specialty
  - `license_number` (string): License number
  - `education` (integer): Education ID
- Optional fields:
  - `experience_years` (integer): Years of experience
  - `bio` (string): Biography
  - `is_available` (boolean): Availability status
  - `is_verified` (boolean): Whether the doctor is verified
  - `identifier_system` (string): FHIR identifier system URI
  - `license_system` (string): FHIR license identifier system URI
  - `communication_languages` (string): Comma-separated list of language codes

#### GET `/api/doctors/{uuid}/`
- Method: GET
- Description: Get doctor details
- No form fields required
- Optional query parameters:
  - `format` (string): Set to 'fhir' to get FHIR-compliant response

#### PUT `/api/doctors/{uuid}/`
- Method: PUT
- Description: Update a doctor (admin only)
- Fields same as POST

#### DELETE `/api/doctors/{uuid}/`
- Method: DELETE
- Description: Delete a doctor (admin only)
- No form fields required

#### POST `/api/doctors/add_profile/`
- Method: POST
- Description: Add doctor profile for verified users
- Required fields:
  - `specialty` (string): Medical specialty
  - `license_number` (string): License number
  - `education` (object): Education details with:
    - `level_of_education` (string): Education level
    - `field` (string): Field of study
    - `institution` (string): Institution
- Optional fields:
  - `experience_years` (integer): Years of experience
  - `bio` (string): Biography
  - `is_available` (boolean): Availability status

#### POST `/api/doctors/admin_add_doctor/`
- Method: POST
- Description: Admin adds a new doctor (creates user and doctor profile)
- Required fields:
  - `username` (string): Username
  - `email` (string): Email address
  - `password` (string): Password
  - `first_name` (string): First name
  - `last_name` (string): Last name
  - `specialty` (string): Medical specialty
  - `license_number` (string): License number
  - `education` (object): Education details with:
    - `level_of_education` (string): Education level
    - `field` (string): Field of study
    - `institution` (string): Institution
- Optional fields:
  - `phone_number` (string): Phone number
  - `address` (string): Address
  - `experience_years` (integer): Years of experience
  - `bio` (string): Biography
  - `is_available` (boolean): Availability status

#### GET `/api/doctors/admin_list_doctors/`
- Method: GET
- Description: Admin lists all doctors
- No form fields required

#### GET `/api/doctors/admin_view_doctor/{uuid}/`
- Method: GET
- Description: Admin views a specific doctor
- No form fields required

#### GET `/api/doctors/admin_list_patients/`
- Method: GET
- Description: Admin lists all patients
- No form fields required
- Optional query parameters:
  - `format` (string): Set to 'fhir' to get FHIR-compliant response

#### GET `/api/doctors/admin_view_patient/{uuid}/`
- Method: GET
- Description: Admin views a specific patient
- No form fields required
- Optional query parameters:
  - `format` (string): Set to 'fhir' to get FHIR-compliant response

## Healthcare App

#### GET `/api/healthcare/`
- Method: GET
- Description: List healthcare facilities
- Optional query parameters:
  - `category` (string): Filter by category
  - `name` (string): Filter by name
  - `active` (boolean): Filter by active status
  - `format` (string): Set to 'fhir' to get FHIR-compliant response

#### POST `/api/healthcare/`
- Method: POST
- Description: Create a healthcare facility (admin only)
- Required fields:
  - `name` (string): Facility name
  - `description` (string): Description
  - `category` (string): Category (choices: 'GENERAL', 'PEDIATRIC', 'MENTAL', 'DENTAL', 'VISION', 'OTHER')
  - `address` (string): Address
  - `phone_number` (string): Phone number
  - `email` (string): Email address
- Optional fields:
  - `website` (string): Website URL
  - `is_verified` (boolean): Verification status
  - `is_active` (boolean): Active status
  - `doctor_ids` (list): List of doctor IDs
  - `identifier_system` (string): FHIR identifier system URI
  - `part_of` (uuid): Parent organization ID
  - `city` (string): City
  - `state` (string): State/Province
  - `postal_code` (string): Postal/ZIP code
  - `country` (string): Country

#### GET `/api/healthcare/{uuid}/`
- Method: GET
- Description: Get healthcare facility details
- No form fields required
- Optional query parameters:
  - `format` (string): Set to 'fhir' to get FHIR-compliant response

#### PUT `/api/healthcare/{uuid}/`
- Method: PUT
- Description: Update a healthcare facility (admin only)
- Fields same as POST

#### DELETE `/api/healthcare/{uuid}/`
- Method: DELETE
- Description: Delete a healthcare facility (admin only)
- No form fields required

#### POST `/api/healthcare/assign_patient_to_doctor/`
- Method: POST
- Description: Admin assigns a patient to a doctor
- Required fields:
  - `patient_id` (uuid): Patient ID
  - `doctor_id` (uuid): Doctor ID
- Optional fields:
  - `notes` (string): Assignment notes
  - `status` (string): Status (choices: 'planned', 'arrived', 'triaged', 'in-progress', 'onleave', 'finished', 'cancelled', 'entered-in-error', 'unknown')
  - `encounter_type` (string): Type (choices: 'AMB', 'EMER', 'FLD', 'HH', 'IMP', 'VR', 'OBS', 'OP', 'SS')
  - `reason` (string): Reason for encounter
  - `healthcare_facility` (uuid): Healthcare facility ID
  - `scheduled_start` (datetime): Scheduled start time
  - `scheduled_end` (datetime): Scheduled end time
  - `actual_start` (datetime): Actual start time
  - `actual_end` (datetime): Actual end time
  - `identifier_system` (string): FHIR identifier system URI

#### GET `/api/healthcare/list_patient_doctor_assignments/`
- Method: GET
- Description: Admin lists patient-doctor assignments
- Optional query parameters:
  - `doctor_id` (uuid): Filter by doctor ID
  - `patient_id` (uuid): Filter by patient ID
  - `format` (string): Set to 'fhir' to get FHIR-compliant response

#### GET `/api/healthcare/view_assignment/{uuid}/`
- Method: GET
- Description: Admin views a specific assignment
- No form fields required
- Optional query parameters:
  - `format` (string): Set to 'fhir' to get FHIR-compliant response

## Authentication Endpoints

#### POST `/api/token/refresh/`
- Method: POST
- Description: Refresh JWT token
- Required fields:
  - `refresh` (string): Refresh token

#### POST `/api/token/verify/`
- Method: POST
- Description: Verify JWT token
- Required fields:
  - `token` (string): JWT token

#### GET `/api/verify-token/`
- Method: GET
- Description: Verify JWT token in header
- No form fields required

## FHIR Endpoints

### FHIR Resources

#### GET `/fhir/Patient/`
- Method: GET
- Description: List all patients in FHIR format
- No form fields required
- Response: FHIR Bundle of Patient resources

#### GET `/fhir/Patient/{uuid}/`
- Method: GET
- Description: Get a specific patient in FHIR format
- No form fields required
- Response: FHIR Patient resource

#### GET `/fhir/Practitioner/`
- Method: GET
- Description: List all doctors in FHIR format
- No form fields required
- Response: FHIR Bundle of Practitioner resources

#### GET `/fhir/Practitioner/{uuid}/`
- Method: GET
- Description: Get a specific doctor in FHIR format
- No form fields required
- Response: FHIR Practitioner resource

#### GET `/fhir/Organization/`
- Method: GET
- Description: List all healthcare facilities in FHIR format
- No form fields required
- Response: FHIR Bundle of Organization resources

#### GET `/fhir/Organization/{uuid}/`
- Method: GET
- Description: Get a specific healthcare facility in FHIR format
- No form fields required
- Response: FHIR Organization resource

#### GET `/fhir/Encounter/`
- Method: GET
- Description: List all patient-doctor assignments in FHIR format
- No form fields required
- Response: FHIR Bundle of Encounter resources

#### GET `/fhir/Encounter/{uuid}/`
- Method: GET
- Description: Get a specific patient-doctor assignment in FHIR format
- No form fields required
- Response: FHIR Encounter resource

#### GET `/fhir/metadata`
- Method: GET
- Description: FHIR capability statement
- No form fields required
- Response: FHIR CapabilityStatement resource