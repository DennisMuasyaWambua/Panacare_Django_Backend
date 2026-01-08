# CHP-Patient Assignment & Messaging Implementation

This document outlines the implementation of admin endpoints for CHP-patient assignment and in-app messaging between CHPs and patients.

## Features Implemented

### 1. Admin CHP-Patient Assignment Endpoint

**Endpoint:** `POST /api/admin/assign-chp-patient/`

**Purpose:** Allows administrators to assign or reassign a Community Health Provider (CHP) to a patient.

**Authentication:** Requires admin role

**Request Body:**
```json
{
    "chp_id": "uuid-of-chp",
    "patient_id": "uuid-of-patient"
}
```

**Response:**
```json
{
    "message": "Patient John Doe successfully assigned to CHP Jane Smith",
    "patient": {
        "id": "patient-uuid",
        "name": "John Doe",
        "email": "john@example.com"
    },
    "chp": {
        "id": "chp-uuid", 
        "name": "Jane Smith",
        "specialization": "Community Health"
    },
    "previous_chp": {
        "id": "previous-chp-uuid",
        "name": "Previous CHP Name"
    }
}
```

**Features:**
- Validates CHP and patient existence
- Tracks previous CHP assignments
- Creates comprehensive audit logs
- Supports both initial assignment and reassignment

### 2. CHP-Patient Messaging System

**Endpoints:**
- `GET /api/messages/` - Retrieve messages
- `POST /api/messages/` - Send a message
- `PATCH /api/messages/{message_id}/read/` - Mark message as read

**Purpose:** Enables secure messaging between CHPs and their assigned patients.

#### Get Messages

**Query Parameters:**
- `patient_id` (for CHPs) - Filter messages for specific patient
- `chp_id` (for patients) - Filter messages for specific CHP

**Response:**
```json
[
    {
        "id": "message-uuid",
        "sender": "sender-user-uuid",
        "recipient": "recipient-user-uuid",
        "patient": "patient-uuid",
        "chp": "chp-uuid",
        "message": "Hello, how are you feeling today?",
        "is_read": false,
        "created_at": "2025-01-08T10:30:00Z",
        "updated_at": "2025-01-08T10:30:00Z",
        "sender_name": "Dr. Jane Smith",
        "recipient_name": "John Doe",
        "patient_name": "John Doe",
        "chp_name": "Dr. Jane Smith"
    }
]
```

#### Send Message

**Request Body:**
```json
{
    "recipient": "recipient-user-uuid",
    "patient": "patient-uuid", 
    "chp": "chp-uuid",
    "message": "Hello, how are you feeling today?"
}
```

**Features:**
- Role-based access (CHPs and patients only)
- Validates sender-recipient relationships
- Automatic sender assignment
- Read status tracking

## Models

### CHPPatientMessage

```python
class CHPPatientMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='messages')
    chp = models.ForeignKey(CommunityHealthProvider, on_delete=models.CASCADE, related_name='messages')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

## Security Features

1. **Role-based Access Control**
   - Admin endpoints require admin role
   - Messaging restricted to CHPs and patients
   - Relationship validation between CHPs and patients

2. **Data Validation**
   - Serializer-based validation for all inputs
   - Existence checks for referenced entities
   - Relationship integrity enforcement

3. **Audit Logging**
   - CHP assignment/reassignment actions logged
   - IP address and user details captured
   - Previous assignments tracked for history

## Database Changes

### Migration: `0010_chppatientmessage.py`
- Creates CHPPatientMessage table
- Establishes foreign key relationships
- Sets up indexes for optimal query performance

## Admin Interface

### CHPPatientMessageAdmin
- List view with sender, recipient, patient, CHP, read status
- Filtering by read status, creation date, and CHP
- Search functionality across users and message content
- Read-only timestamp fields

## Usage Examples

### Assigning CHP to Patient (Admin)

```bash
curl -X POST \
  http://localhost:8000/api/admin/assign-chp-patient/ \
  -H 'Authorization: Bearer {admin-token}' \
  -H 'Content-Type: application/json' \
  -d '{
    "chp_id": "chp-uuid-here",
    "patient_id": "patient-uuid-here"
  }'
```

### CHP Sending Message to Patient

```bash
curl -X POST \
  http://localhost:8000/api/messages/ \
  -H 'Authorization: Bearer {chp-token}' \
  -H 'Content-Type: application/json' \
  -d '{
    "recipient": "patient-user-uuid",
    "patient": "patient-uuid", 
    "chp": "chp-uuid",
    "message": "Hello! How are you feeling today?"
  }'
```

### Patient Retrieving Messages

```bash
curl -X GET \
  http://localhost:8000/api/messages/?chp_id=chp-uuid \
  -H 'Authorization: Bearer {patient-token}'
```

## Integration with Existing System

The implementation integrates seamlessly with the existing Panacare healthcare system:

1. **Uses existing User and Role models** for authentication
2. **Leverages existing Patient and CommunityHealthProvider models**
3. **Follows existing API patterns** and response formats
4. **Integrates with audit logging system**
5. **Maintains FHIR compliance** architecture
6. **Uses existing permission classes** and authentication

## Testing

A comprehensive test script has been created at `test_chp_messaging.py` to verify:
- Model field definitions
- Endpoint URL registration
- Serializer functionality

To run tests:
```bash
python3 test_chp_messaging.py
```

## Future Enhancements

Potential improvements for the messaging system:

1. **Message attachments** (images, files)
2. **Push notifications** via FCM
3. **Message encryption** for additional security
4. **Bulk messaging** capabilities for CHPs
5. **Message threading/conversations**
6. **Read receipts** and delivery confirmations
7. **Message search** and filtering
8. **Integration with appointment system**

## Dependencies

No additional dependencies were required. The implementation uses existing Django and DRF components already in the project.