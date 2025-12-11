# Audit Logs API Documentation

This document provides an overview of the Audit Logs API endpoints that have been implemented for the Panacare Healthcare Backend.

## Overview

The Audit Logs API provides comprehensive tracking of user activities within the system for security, compliance, and monitoring purposes. All endpoints require admin-level authentication.

## Authentication

All audit log endpoints require authentication with a JWT token and admin role. Include the token in the Authorization header:

```
Authorization: Bearer <your_admin_jwt_token>
```

## API Endpoints

### Base URL: `/api/audit-logs/`

#### 1. List Audit Logs
- **URL**: `GET /api/audit-logs/`
- **Description**: Retrieve a paginated list of all audit logs
- **Permissions**: Admin users only
- **Response**: Paginated list of audit log entries

#### 2. Retrieve Audit Log
- **URL**: `GET /api/audit-logs/{id}/`
- **Description**: Retrieve a specific audit log by ID
- **Permissions**: Admin users only
- **Response**: Single audit log entry

#### 3. Export to CSV
- **URL**: `GET /api/audit-logs/export-csv/`
- **Description**: Export audit logs to CSV format
- **Permissions**: Admin users only
- **Response**: CSV file download

#### 4. Export to PDF
- **URL**: `GET /api/audit-logs/export-pdf/`
- **Description**: Export audit logs to PDF format (HTML for printing)
- **Permissions**: Admin users only
- **Response**: HTML file for PDF conversion

#### 5. Statistics
- **URL**: `GET /api/audit-logs/statistics/`
- **Description**: Get audit log statistics and analytics
- **Permissions**: Admin users only
- **Response**: Statistical summary of audit logs

## Query Parameters

All list endpoints support the following query parameters for filtering and searching:

### Search and Filtering
- `search`: Search by username or email address
- `activity`: Filter by activity type (login, logout, profile_update, etc.)
- `status`: Filter by user status (active, inactive, suspended, pending)
- `role`: Filter by user role (admin, doctor, patient)
- `date_from`: Filter from date (YYYY-MM-DD format)
- `date_to`: Filter to date (YYYY-MM-DD format)

### Ordering
- `ordering`: Order results by field
  - `-created_at`: Newest first (default)
  - `created_at`: Oldest first
  - `-last_active`: Most recently active first
  - `last_active`: Least recently active first
  - `username`: Username A-Z
  - `-username`: Username Z-A

### Pagination
- `page`: Page number
- `page_size`: Number of items per page

## Example Usage

### Basic List Request
```bash
GET /api/audit-logs/
```

### Search for Admin Activities
```bash
GET /api/audit-logs/?search=admin&activity=login
```

### Filter by Role and Status
```bash
GET /api/audit-logs/?role=patient&status=active
```

### Date Range Filter
```bash
GET /api/audit-logs/?date_from=2025-01-01&date_to=2025-12-31
```

### Complex Query with Multiple Filters
```bash
GET /api/audit-logs/?activity=user_create&role=admin&ordering=-created_at&page_size=50
```

### Export Data
```bash
GET /api/audit-logs/export-csv/?role=patient&date_from=2025-01-01
```

## Response Format

### List Response
```json
{
  "count": 100,
  "next": "http://api.example.com/audit-logs/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid-here",
      "username": "admin_user",
      "activity": "login",
      "activity_display": "Logged In",
      "email_address": "admin@example.com",
      "role": "admin",
      "time_spent": "PT2M",
      "formatted_time_spent": "2m",
      "date_joined": "2025-01-01T00:00:00Z",
      "last_active": "2025-08-25T09:30:00Z",
      "status": "active",
      "status_display": "Active",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "session_id": "session123",
      "details": {
        "login_method": "web",
        "browser": "Chrome"
      },
      "created_at": "2025-08-25T09:30:00Z",
      "updated_at": "2025-08-25T09:30:00Z",
      "full_name": "Admin User",
      "formatted_created_at": "25 August 2025",
      "formatted_last_active": "25 August 2025",
      "formatted_date_joined": "01 January 2025"
    }
  ]
}
```

### Statistics Response
```json
{
  "total_logs": 1500,
  "today_logs": 45,
  "week_logs": 320,
  "activity_breakdown": [
    {"activity": "login", "count": 450},
    {"activity": "profile_update", "count": 230},
    {"activity": "appointment_create", "count": 180}
  ],
  "status_breakdown": [
    {"status": "active", "count": 1350},
    {"status": "inactive", "count": 150}
  ],
  "role_breakdown": [
    {"role": "patient", "count": 800},
    {"role": "doctor", "count": 450},
    {"role": "admin", "count": 250}
  ]
}
```

## Activity Types

The following activity types are tracked:

- `login` - User logged in
- `logout` - User logged out
- `register` - User registration
- `profile_update` - Profile updated
- `password_change` - Password changed
- `appointment_create` - Appointment created
- `appointment_update` - Appointment updated
- `appointment_cancel` - Appointment cancelled
- `consultation_start` - Consultation started
- `consultation_end` - Consultation ended
- `article_create` - Article created
- `article_update` - Article updated
- `article_approve` - Article approved
- `article_reject` - Article rejected
- `user_create` - User created
- `user_update` - User updated
- `user_delete` - User deleted
- `role_assign` - Role assigned
- `subscription_create` - Subscription created
- `payment_process` - Payment processed
- `data_export` - Data exported
- `system_access` - System access
- `api_access` - API access
- `other` - Other activity

## Status Types

- `active` - Active user
- `inactive` - Inactive user
- `suspended` - Suspended user
- `pending` - Pending verification

## Data Model

The AuditLog model includes the following fields:

- `id` (UUID): Unique identifier
- `user` (ForeignKey): Reference to the user
- `username` (CharField): Username at time of activity
- `activity` (CharField): Type of activity performed
- `email_address` (EmailField): Email at time of activity
- `role` (CharField): User roles at time of activity
- `time_spent` (DurationField): Time spent on activity (optional)
- `date_joined` (DateTimeField): When user joined the system
- `last_active` (DateTimeField): Last activity timestamp
- `status` (CharField): User status
- `ip_address` (GenericIPAddressField): User's IP address (optional)
- `user_agent` (TextField): Browser user agent (optional)
- `session_id` (CharField): Session identifier (optional)
- `details` (JSONField): Additional activity details
- `created_at` (DateTimeField): When log entry was created
- `updated_at` (DateTimeField): When log entry was last updated

## Security Considerations

1. **Admin Only Access**: All audit log endpoints are restricted to admin users only
2. **Read-Only**: Audit logs cannot be modified or deleted through the API
3. **Comprehensive Logging**: All user activities are tracked for security compliance
4. **Data Retention**: Consider implementing data retention policies for audit logs
5. **IP Tracking**: User IP addresses are logged for security analysis

## Integration with Frontend

The audit logs are designed to match the provided UI design with:

- Search functionality by name/email
- Filter by role, status, activity type, and date
- Export capabilities (CSV/PDF)
- Detailed view of each log entry
- Statistics and analytics dashboard

## Testing

Sample data and test endpoints have been created. To test:

1. Run `python test_audit_api.py` to create sample data
2. Start the Django server: `python manage.py runserver`
3. Login as admin user to get JWT token
4. Use the token to access audit log endpoints
5. Check Swagger documentation at `/swagger/` for interactive testing

## Admin Interface

Audit logs are also available in the Django admin interface at `/admin/` with:
- List view with filtering and search
- Read-only access to prevent tampering
- Date hierarchy for easy navigation
- Detailed view of each log entry