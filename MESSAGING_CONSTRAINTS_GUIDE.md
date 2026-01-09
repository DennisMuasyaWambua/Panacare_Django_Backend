# CHP-Patient Messaging Constraints & API Reference

## Assignment Results Summary ✅

**CHP Email:** `54bhyh6kgi@mrotzis.com`  
**CHP ID:** `29282674-e223-4b17-89ec-4622e70022a1`  
**Total Assigned Patients:** 8

**Newly Assigned Patients:**
1. John Doe (`3c653da8-2da4-4d8c-bdcf-3bc1d7d3b3da`) - sehileb688@dlbazi.com
2. Mustafa Alsayed (`918a434e-5692-42ae-8d76-a396e5801607`) - mustafaalsayed@mypanacare.com  
3. ogun shogun (`f2451e7b-db13-4790-9d70-848df1b78bdb`) - hn837hnsr6@ibolinva.com
4. Fris Bee (`409d45ca-3c68-4f34-bfeb-bf06cec33350`) - yiliy22638@frisbook.com
5. Patient Zero (`05c12da2-1010-4af7-835b-2603efa110bf`) - botayir383@dlbazi.com

## Messaging API Constraints & Specifications

### 1. Database Field Constraints

#### CHPPatientMessage Model Fields:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUIDField | Primary Key, Auto-generated | Message unique identifier |
| `sender` | ForeignKey(User) | Required, CASCADE delete | Message sender (CHP or Patient user) |
| `recipient` | ForeignKey(User) | Required, CASCADE delete | Message recipient (CHP or Patient user) |
| `patient` | ForeignKey(Patient) | Required, CASCADE delete | Patient involved in conversation |
| `chp` | ForeignKey(CommunityHealthProvider) | Required, CASCADE delete | CHP involved in conversation |
| `message` | TextField | **No length limit**, Required | Message content |
| `is_read` | BooleanField | Default: False | Read status |
| `created_at` | DateTimeField | Auto-generated | Message creation timestamp |
| `updated_at` | DateTimeField | Auto-updated | Last modification timestamp |

### 2. API Request Constraints

#### POST /api/messages/ (Send Message)

**Required Headers:**
```http
Authorization: Bearer <jwt-token>
Content-Type: application/json
```

**Request Body Schema:**
```json
{
  "recipient": "uuid",        // REQUIRED: UUID of recipient user
  "patient": "uuid",          // REQUIRED: UUID of patient 
  "chp": "uuid",             // REQUIRED: UUID of CHP
  "message": "string"        // REQUIRED: Message content
}
```

**Field Validations:**

| Field | Datatype | Length Limit | Required | Validation Rules |
|-------|----------|-------------|----------|------------------|
| `recipient` | UUID String | 36 chars | ✅ Yes | Must be valid UUID, user must exist |
| `patient` | UUID String | 36 chars | ✅ Yes | Must be valid UUID, patient must exist |
| `chp` | UUID String | 36 chars | ✅ Yes | Must be valid UUID, CHP must exist |
| `message` | String | **Unlimited** | ✅ Yes | Cannot be empty, trimmed |

**Additional Business Logic Constraints:**

1. **Sender Auto-Assignment:** `sender` field automatically set to authenticated user
2. **Role Validation:** Only users with 'chp' or 'patient' roles can send messages
3. **Relationship Validation:**
   - If sender is CHP: recipient must be the patient user
   - If sender is Patient: recipient must be the CHP user
   - Patient and CHP must have an existing assignment relationship

#### GET /api/messages/ (Retrieve Messages)

**Query Parameters:**

| Parameter | Type | Required | Description | Constraints |
|-----------|------|----------|-------------|-------------|
| `patient_id` | UUID | Optional | Filter by patient (CHP users only) | Valid UUID |
| `chp_id` | UUID | Optional | Filter by CHP (Patient users only) | Valid UUID |

**Response Pagination:** Not implemented (returns all matching messages)

#### PATCH /api/messages/{message_id}/read/ (Mark as Read)

**URL Parameters:**
- `message_id`: UUID of the message (required)

**Constraints:**
- Only message recipient can mark as read
- Message must exist and belong to authenticated user

### 3. Authentication & Authorization Constraints

#### Required Permissions:
- **Send Message:** User must have 'chp' or 'patient' role
- **View Messages:** User must have 'chp' or 'patient' role  
- **Mark as Read:** User must be the message recipient

#### JWT Token Requirements:
- Valid, non-expired JWT token in Authorization header
- User must be active and verified

### 4. Message Content Constraints

#### Message Field Specifications:
- **Type:** Django TextField (unlimited length)
- **Database Storage:** PostgreSQL TEXT type (up to 1GB theoretical limit)
- **Practical Limits:** 
  - Recommended max: 10,000 characters for performance
  - JSON serialization limit: ~16MB per request
  - Browser/mobile app limits may apply

#### Content Restrictions:
- No HTML/JavaScript validation (plain text)
- No profanity filtering implemented
- No attachment support (text only)
- Unicode/emoji support: Full UTF-8

### 5. Rate Limiting & Performance

#### Current Implementation:
- **No rate limiting** implemented
- **No pagination** for message retrieval
- **No message caching**

#### Recommendations for Production:
```python
# Example rate limiting (not implemented)
# 100 messages per hour per user
# 1000 message retrievals per hour per user
```

### 6. Example API Calls

#### CHP Sending Message to Patient:
```bash
curl -X POST http://localhost:8000/api/messages/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "3c653da8-2da4-4d8c-bdcf-3bc1d7d3b3da",
    "patient": "3c653da8-2da4-4d8c-bdcf-3bc1d7d3b3da", 
    "chp": "29282674-e223-4b17-89ec-4622e70022a1",
    "message": "Hello John! How are you feeling today? Please let me know if you need any assistance."
  }'
```

#### Patient Retrieving Messages:
```bash
curl -X GET "http://localhost:8000/api/messages/?chp_id=29282674-e223-4b17-89ec-4622e70022a1" \
  -H "Authorization: Bearer patient_jwt_token_here"
```

#### Mark Message as Read:
```bash
curl -X PATCH "http://localhost:8000/api/messages/message-uuid-here/read/" \
  -H "Authorization: Bearer jwt_token_here"
```

### 7. Error Response Examples

#### Invalid Relationship:
```json
{
  "error": "Recipient must be the patient"
}
```

#### Permission Denied:
```json
{
  "error": "Only CHPs and patients can send messages"
}
```

#### Validation Error:
```json
{
  "patient": ["This field is required."],
  "message": ["This field may not be blank."]
}
```

### 8. Response Format

#### Successful Message Send:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "sender": "f50a504d-cfa5-43aa-9004-95670967aa35",
  "recipient": "3c653da8-2da4-4d8c-bdcf-3bc1d7d3b3da",
  "patient": "3c653da8-2da4-4d8c-bdcf-3bc1d7d3b3da",
  "chp": "29282674-e223-4b17-89ec-4622e70022a1",
  "message": "Hello John! How are you feeling today?",
  "is_read": false,
  "created_at": "2025-01-08T09:45:30.123456Z",
  "updated_at": "2025-01-08T09:45:30.123456Z",
  "sender_name": "",
  "recipient_name": "John Doe",
  "patient_name": "John Doe", 
  "chp_name": ""
}
```

### 9. Security Considerations

#### Data Protection:
- Messages stored in PostgreSQL with standard Django security
- No encryption at rest (plaintext in database)
- JWT tokens provide authentication security
- HTTPS recommended for transport security

#### Privacy Controls:
- Users can only see their own conversations
- No message editing after send
- No message deletion through API (admin only)
- Read receipts only visible to conversation participants

### 10. Database Migration Status

**Migration Required:** `users/migrations/0010_chppatientmessage.py`

To apply the migration:
```bash
python3 manage.py migrate users
```

**Note:** The CHPPatientMessage table needs to be created before messaging functionality works completely.