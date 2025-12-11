
# Backend API Features

This document outlines the key features implemented in the Panacare Healthcare Backend API.

## User Management

- **Authentication:** User registration, login, and activation via email. JWT-based authentication for secure API access.
- **Role-Based Access Control (RBAC):** API endpoints for creating and managing user roles (e.g., Admin, Doctor, Patient).
- **User Profiles:** Endpoints for managing user and patient profiles, including personal information, contact details, and medical history.
- **Account Management:** Features for changing passwords, email addresses, and phone numbers, as well as a password reset functionality.

## Doctor Management

- **Doctor Profiles:** Comprehensive doctor profiles that include specialty, education, license information, and availability.
- **Admin Operations:** Admins can add, list, view, and verify doctors in the system.

## Healthcare & Consultations

- **Appointments:** Create, manage, and list appointments between patients and doctors.
- **Consultations:** Endpoints for managing medical consultations, including teleconsultation logging.
- **Doctor Availability:** Doctors can set and manage their availability for appointments.
- **Patient-Doctor Assignment:** Functionality to assign patients to specific doctors.

## Subscriptions and Payments

- **Subscription Packages:** Management of different subscription packages for patients.
- **Patient Subscriptions:** Endpoints for handling patient subscriptions to packages.
- **Payments:** API for processing payments for subscriptions and other services.

## Clinical Support

- **Clinical Decision Support:** An API to provide clinical decision support to healthcare professionals.
- **Patient History:** An endpoint to retrieve a patient's clinical history.

## Content and Engagement

- **Articles:** A simple CMS for creating and managing health-related articles.
- **Comments:** Users can comment on articles.
- **Doctor Ratings:** Patients can rate doctors to provide feedback.

## Auditing and Monitoring

- **Audit Logs:** The system keeps a log of important actions for auditing purposes.
- **Risk Segmentation:** API for patient risk segmentation.
- **Follow-up Compliance:** Tracking and managing patient follow-up compliance.

## Miscellaneous

- **Contact Us & Support:** Endpoints for users to send contact requests and support tickets.
- **API Documentation:** The API is self-documented using Swagger/OpenAPI, available at the `/swagger/` endpoint.
