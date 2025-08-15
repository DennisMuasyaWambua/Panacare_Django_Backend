# Panacare Healthcare Backend (Django)

This is a Django REST Framework implementation of the Panacare Healthcare Backend.

## Features

- User authentication and management
- Email verification for new accounts
- Doctor profiles and management
- Healthcare facility management
- RESTful API endpoints for all resources
- Class-based views with Django REST Framework
- FHIR-compliant API endpoints

## API Endpoints

### Users
- `GET /api/users/` - List all users
- `POST /api/users/` - Create a new user
- `GET /api/users/{id}/` - Get user details
- `PUT /api/users/{id}/` - Update user details
- `DELETE /api/users/{id}/` - Delete user
- `POST /api/users/register/` - Register a new user (sends activation email)
- `GET /api/users/activate/{uidb64}/{token}/` - Activate user account
- `POST /api/users/login/` - Login user

### Roles
- `GET /api/roles/` - List all roles
- `POST /api/roles/` - Create a new role
- `GET /api/roles/{id}/` - Get role details
- `PUT /api/roles/{id}/` - Update role details
- `DELETE /api/roles/{id}/` - Delete role

### Patients
- `GET /api/patients/` - List all patients
- `POST /api/patients/` - Create a new patient
- `GET /api/patients/{id}/` - Get patient details
- `PUT /api/patients/{id}/` - Update patient details
- `DELETE /api/patients/{id}/` - Delete patient

### Doctors
- `GET /api/doctors/` - List all doctors
- `POST /api/doctors/` - Create a new doctor
- `GET /api/doctors/{id}/` - Get doctor details
- `PUT /api/doctors/{id}/` - Update doctor details
- `DELETE /api/doctors/{id}/` - Delete doctor

### Healthcare Facilities
- `GET /api/healthcare/` - List all healthcare facilities
- `POST /api/healthcare/` - Create a new healthcare facility
- `GET /api/healthcare/{id}/` - Get healthcare facility details
- `PUT /api/healthcare/{id}/` - Update healthcare facility details
- `DELETE /api/healthcare/{id}/` - Delete healthcare facility
- `POST /api/healthcare/assign_patient_to_doctor/` - Admin assign patient to doctor
- `GET /api/healthcare/list_patient_doctor_assignments/` - Admin list assignments
- `GET /api/healthcare/view_assignment/{id}/` - Admin view specific assignment
- `GET /api/healthcare/doctor/patients/` - Doctor view assigned patients
- `GET /api/healthcare/doctor/patient/{id}/` - Doctor view specific patient

### Appointments
- `GET /api/appointments/` - List appointments
- `POST /api/appointments/` - Create appointment
- `GET /api/appointments/{id}/` - Get specific appointment
- `PUT /api/appointments/{id}/` - Update appointment
- `DELETE /api/appointments/{id}/` - Delete appointment
- `GET /api/appointments/my_appointments/` - Patient view own appointments
- `GET /api/appointments/doctor_appointments/` - Doctor view own appointments
- `POST /api/appointments/{id}/cancel_appointment/` - Patient cancel appointment
- `POST /api/appointments/{id}/patient_reschedule/` - Patient reschedule appointment
- `POST /api/appointments/{id}/doctor_reschedule/` - Doctor reschedule appointment
- `POST /api/appointments/{id}/update_consultation_details/` - Doctor update consultation

### Consultations
- `GET /api/consultations/` - List consultations
- `POST /api/consultations/` - Create consultation
- `GET /api/consultations/{id}/` - Get specific consultation
- `PUT /api/consultations/{id}/` - Update consultation
- `DELETE /api/consultations/{id}/` - Delete consultation
- `POST /api/consultations/{id}/start_consultation/` - Doctor start consultation
- `POST /api/consultations/{id}/end_consultation/` - Doctor end consultation
- `GET /api/consultations/{id}/get_token/` - Get Twilio token for video call
- `POST /api/consultations/{id}/join_consultation/` - Join/rejoin consultation
- `GET /api/consultations/{id}/chat_messages/` - Get chat messages
- `POST /api/consultations/{id}/send_message/` - Send chat message
- `POST /api/consultations/{id}/mark_messages_read/` - Mark messages as read

### Packages & Subscriptions
- `GET /api/packages/` - List all available subscription packages
- `POST /api/packages/` - Create new package (admin only)
- `GET /api/packages/{id}/` - Get specific package details
- `PUT /api/packages/{id}/` - Update package (admin only)
- `DELETE /api/packages/{id}/` - Delete package (admin only)
- `GET /api/subscriptions/` - List subscriptions
- `POST /api/subscriptions/subscribe/` - Create subscription with payment
- `GET /api/subscriptions/active/` - Get patient's active subscription
- `POST /api/subscriptions/{id}/cancel/` - Cancel subscription
- `POST /api/subscriptions/upgrade/` - Upgrade subscription
- `POST /api/subscriptions/downgrade/` - Downgrade subscription
- `POST /api/subscriptions/{id}/renew/` - Renew subscription
- `GET /api/subscriptions/{id}/usage/` - Get subscription usage statistics

### Payments
- `GET /api/payments/` - List payments
- `POST /api/payments/` - Create payment
- `GET /api/payments/{id}/` - Get specific payment
- `PUT /api/payments/{id}/` - Update payment
- `DELETE /api/payments/{id}/` - Delete payment
- `POST /api/payments/{id}/process/` - Process payment via Pesapal
- `POST /api/payments/{id}/callback/` - Payment callback from Pesapal
- `POST /api/payments/ipn/` - Instant Payment Notification from Pesapal
- `GET /api/payments/{id}/status/` - Check payment status

### Doctor Availability
- `GET /api/doctor-availability/` - List doctor availability
- `POST /api/doctor-availability/` - Create availability slot
- `GET /api/doctor-availability/{id}/` - Get specific availability
- `PUT /api/doctor-availability/{id}/` - Update availability
- `DELETE /api/doctor-availability/{id}/` - Delete availability
- `GET /api/doctor-availability/{doctor_id}/` - Get availability by doctor ID
- `GET /api/doctor-availability/my_availability/` - Doctor view own availability

### Doctor Ratings & Reviews
- `GET /api/doctor-ratings/` - List doctor ratings
- `POST /api/doctor-ratings/` - Create doctor rating
- `GET /api/doctor-ratings/{id}/` - Get specific rating
- `PUT /api/doctor-ratings/{id}/` - Update rating
- `DELETE /api/doctor-ratings/{id}/` - Delete rating
- `GET /api/doctor-ratings/doctor_average_rating/` - Get doctor's average rating
- `GET /api/doctors/{id}/ratings/` - Get doctor ratings
- `GET /api/doctors/{id}/rating_summary/` - Get doctor rating summary
- `POST /api/doctors/{id}/review/` - Patient review doctor

### Articles & Content Management
- `GET /api/articles/` - List articles
- `POST /api/articles/` - Create article
- `GET /api/articles/{id}/` - Get specific article
- `PUT /api/articles/{id}/` - Update article
- `DELETE /api/articles/{id}/` - Delete article
- `POST /api/articles/{id}/approve/` - Admin approve article
- `POST /api/articles/{id}/reject/` - Admin reject article
- `POST /api/articles/{id}/publish/` - Publish approved article
- `POST /api/articles/{id}/unpublish/` - Unpublish article
- `POST /api/articles/{id}/view/` - Increment article view count
- `GET /api/articles/my_articles/` - Doctor view own articles
- `GET /api/articles/featured/` - Get featured articles
- `GET /api/articles/popular/` - Get popular articles
- `GET /api/articles/recent/` - Get recent articles
- `GET /api/articles/by_condition/` - Get articles by health condition
- `GET /api/articles/{id}/export_word/` - Export article to Word document

### Article Comments
- `GET /api/article-comments/` - List article comments
- `POST /api/article-comments/` - Create comment
- `GET /api/article-comments/{id}/` - Get specific comment
- `PUT /api/article-comments/{id}/` - Update comment
- `DELETE /api/article-comments/{id}/` - Delete comment
- `POST /api/article-comments/{id}/like/` - Like comment
- `POST /api/article-comments/{id}/unlike/` - Unlike comment
- `POST /api/article-comments/{id}/reply/` - Reply to comment

### Clinical Decision Support
- `POST /api/clinical-decision/` - Process clinical data and get recommendations
- `GET /api/clinical-history/` - Get patient's clinical decision history

### Authentication & Password Management
- `POST /api/forgot-password/` - Request password reset
- `POST /api/reset-password/{uidb64}/{token}/` - Reset password
- `POST /api/users/resend-verification/` - Resend verification email
- `POST /api/users/change-password/` - Change password
- `POST /api/users/change-email/` - Change email
- `POST /api/users/change-phone/` - Change phone number
- `POST /api/token/refresh/` - JWT token refresh
- `POST /api/token/verify/` - JWT token verification

### Doctor Management (Enhanced)
- `POST /api/doctors/add_profile/` - Add doctor profile for verified users
- `GET /api/doctors/profile/` - Get doctor's own profile
- `POST /api/doctors/admin_add_doctor/` - Admin add doctor (creates user + doctor)
- `GET /api/doctors/admin_list_doctors/` - Admin list all doctors
- `GET /api/doctors/admin_view_doctor/{id}/` - Admin view specific doctor
- `PATCH /api/doctors/{id}/verify/` - Admin verify doctor
- `GET /api/doctors/admin_list_patients/` - Admin list all patients
- `GET /api/doctors/admin_view_patient/{id}/` - Admin view specific patient

### Support & Communication
- `POST /api/contact-us/` - Contact us form submission
- `POST /api/support-request/` - Support request submission

### FHIR API Access
You can access all endpoints in FHIR format by adding the `format=fhir` query parameter:

- `GET /api/patients/?format=fhir` - List all patients in FHIR Patient format
- `GET /api/patients/{id}/?format=fhir` - Get a specific patient in FHIR Patient format
- `GET /api/doctors/?format=fhir` - List all doctors in FHIR Practitioner format
- `GET /api/doctors/{id}/?format=fhir` - Get a specific doctor in FHIR Practitioner format
- `GET /api/healthcare/?format=fhir` - List all healthcare facilities in FHIR Organization format
- `GET /api/healthcare/{id}/?format=fhir` - Get a specific healthcare facility in FHIR Organization format

Additional FHIR endpoints:
- `GET /fhir/metadata` - FHIR capability statement (returns CapabilityStatement resource)

For more detailed information about the FHIR implementation, see the [FHIR Documentation](README-FHIR.md).

## Setup and Installation

1. Clone the repository
2. Create a virtual environment: `python3 -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run migrations: `python manage.py migrate`
6. Create superuser: `python manage.py createsuperuser`
7. Run the server: `python manage.py runserver`

## Environment Variables

Update the `.env` file with your configuration:

```
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database configuration (optional, defaults to SQLite)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=panacare
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# Email configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=your_email@gmail.com
```

> **Note for Gmail users**: For `EMAIL_HOST_PASSWORD`, you'll need to use an App Password, not your regular Google password. You can generate an App Password in your Google Account settings under Security > 2-Step Verification > App passwords.