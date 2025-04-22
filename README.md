# Panacare Healthcare Backend (Django)

This is a Django REST Framework implementation of the Panacare Healthcare Backend.

## Features

- User authentication and management
- Email verification for new accounts
- Doctor profiles and management
- Healthcare facility management
- RESTful API endpoints for all resources
- Class-based views with Django REST Framework

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

### Customers
- `GET /api/customers/` - List all customers
- `POST /api/customers/` - Create a new customer
- `GET /api/customers/{id}/` - Get customer details
- `PUT /api/customers/{id}/` - Update customer details
- `DELETE /api/customers/{id}/` - Delete customer

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