# Pesapal Subscription Integration Guide

This guide explains how to use the complete Pesapal subscription handling system implemented for the Panacare Healthcare Backend.

## Features Implemented

### ✅ Complete Pesapal Integration
- **Authentication**: Automatic token management with caching
- **Payment Processing**: Submit order requests to Pesapal API
- **Status Verification**: Real-time payment status checking
- **Webhook Handling**: IPN (Instant Payment Notification) support
- **Recurring Payments**: Support for subscription-based payments

### ✅ Subscription Management
- **Create Subscriptions**: Patients can subscribe to healthcare packages
- **Payment Processing**: Integrated with Pesapal for secure payments
- **Subscription Renewal**: Automatic and manual renewal options
- **Upgrade/Downgrade**: Change subscription tiers with prorated billing
- **Cancellation**: Cancel active subscriptions
- **Usage Tracking**: Monitor consultation usage and remaining benefits

### ✅ Management Commands
- **Expire Subscriptions**: Automatically mark expired subscriptions
- **Check Renewals**: Monitor subscriptions nearing expiration
- **Sync Payments**: Synchronize payment status with Pesapal

## API Endpoints

### Subscription Endpoints

#### 1. Create Subscription
```http
POST /api/subscriptions/subscribe/
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "package_id": 1,
  "payment_method": "pesapal",
  "subscription_frequency": "MONTHLY"
}
```

**Response:**
```json
{
  "subscription": {
    "id": 1,
    "patient": 1,
    "package": 1,
    "status": "pending",
    "start_date": "2025-07-03",
    "end_date": "2025-08-03"
  },
  "payment_reference": "PAY_ABC123",
  "payment_id": 1,
  "payment_url": "/api/payments/1/process/",
  "message": "Subscription created. Please complete payment."
}
```

#### 2. Get Active Subscription
```http
GET /api/subscriptions/active/
Authorization: Bearer {jwt_token}
```

#### 3. Upgrade Subscription
```http
POST /api/subscriptions/upgrade/
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "package_id": 2
}
```

#### 4. Downgrade Subscription
```http
POST /api/subscriptions/downgrade/
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "package_id": 1
}
```

#### 5. Renew Subscription
```http
POST /api/subscriptions/{id}/renew/
Authorization: Bearer {jwt_token}
```

#### 6. Cancel Subscription
```http
POST /api/subscriptions/{id}/cancel/
Authorization: Bearer {jwt_token}
```

#### 7. Get Usage Statistics
```http
GET /api/subscriptions/{id}/usage/
Authorization: Bearer {jwt_token}
```

### Payment Endpoints

#### 1. Process Payment
```http
POST /api/payments/{id}/process/
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "payment_id": 1,
  "payment_reference": "PAY_ABC123",
  "amount": "1000.00",
  "currency": "KES",
  "payment_method": "pesapal",
  "redirect_url": "https://cybqa.pesapal.com/pesapalv3/...",
  "order_tracking_id": "abc-123-def",
  "message": "Payment processing initiated. You will be redirected to Pesapal."
}
```

#### 2. Payment Callback
```http
POST /api/payments/{id}/callback/
Content-Type: application/json

{
  "OrderTrackingId": "abc-123-def",
  "OrderMerchantReference": "SUB_1_1"
}
```

#### 3. Payment IPN (Webhook)
```http
POST /api/payments/ipn/
Content-Type: application/json

{
  "OrderTrackingId": "abc-123-def",
  "OrderMerchantReference": "SUB_1_1",
  "OrderNotificationType": "RECURRING"
}
```

#### 4. Check Payment Status
```http
GET /api/payments/{id}/status/
Authorization: Bearer {jwt_token}
```

## Environment Configuration

Add these variables to your `.env` file:

```env
# Pesapal Configuration
PESAPAL_CONSUMER_KEY=your_consumer_key
PESAPAL_CONSUMER_SECRET=your_consumer_secret
PESAPAL_SANDBOX=True  # Set to False for production
PESAPAL_CALLBACK_URL=http://localhost:3000/payment/callback
PESAPAL_IPN_URL=https://your-domain.com/api/payments/pesapal/ipn
PESAPAL_IPN_ID=your_ipn_id  # Obtained after registering IPN URL

# Frontend URL for payment callbacks
FRONTEND_URL=http://localhost:3000
```

## Setup Instructions

### 1. Install Dependencies
The implementation uses Django's built-in libraries and the `requests` library for HTTP calls.

### 2. Configure Pesapal Account
1. Create a Pesapal merchant account
2. Get your Consumer Key and Consumer Secret
3. Register your IPN URL with Pesapal
4. Update your `.env` file with the credentials

### 3. Register IPN URL
Use the Pesapal client to register your IPN URL:

```python
from healthcare.pesapal_client import PesapalClient

client = PesapalClient()
result = client.register_ipn_url(
    "https://your-domain.com/api/payments/ipn/",
    "POST"
)
```

### 4. Run Management Commands

#### Check Django Configuration
```bash
python manage.py check
```

#### Create Subscriptions Management Commands
```bash
# Mark expired subscriptions
python manage.py manage_subscriptions --expire-subscriptions

# Check for renewals in next 7 days
python manage.py manage_subscriptions --check-renewals --days-ahead 7

# Sync payment status with Pesapal
python manage.py manage_subscriptions --sync-payments
```

## Payment Flow

### 1. Patient Subscription Flow
1. **Patient selects package** → POST `/api/subscriptions/subscribe/`
2. **System creates subscription** → Status: `pending`
3. **System creates payment** → Status: `pending`
4. **Patient processes payment** → POST `/api/payments/{id}/process/`
5. **System redirects to Pesapal** → Patient completes payment
6. **Pesapal sends callback** → POST `/api/payments/{id}/callback/`
7. **System activates subscription** → Status: `active`

### 2. Recurring Payment Flow
1. **Pesapal processes recurring payment** → Automatic based on subscription settings
2. **Pesapal sends IPN** → POST `/api/payments/ipn/`
3. **System extends subscription** → Adds duration to end_date
4. **System creates new payment record** → For tracking

### 3. Upgrade/Downgrade Flow
1. **Patient requests upgrade** → POST `/api/subscriptions/upgrade/`
2. **System calculates proration** → Based on remaining days
3. **System creates new payment** → For difference amount
4. **Patient completes payment** → Through Pesapal
5. **System activates new tier** → Immediately after payment

## Database Models

### PatientSubscription
- `patient`: ForeignKey to Patient
- `package`: ForeignKey to Package
- `payment`: ForeignKey to Payment
- `status`: Choice field (pending, active, expired, cancelled, scheduled)
- `start_date`: DateField
- `end_date`: DateField
- `consultations_used`: IntegerField

### Payment
- `reference`: Unique payment reference
- `amount`: Decimal amount
- `currency`: Currency code (default: KES)
- `payment_method`: Payment method (default: pesapal)
- `status`: Choice field (pending, processing, completed, failed, cancelled, refunded)
- `gateway_transaction_id`: Pesapal order tracking ID
- `gateway_response`: JSON response from Pesapal

### Package
- `name`: Package name
- `description`: Package description
- `price`: Package price
- `duration_days`: Subscription duration in days
- `max_consultations`: Maximum consultations allowed
- `features`: JSON field for additional features

## Testing

### 1. Test Pesapal Integration
```python
# Run the test script
python test_pesapal.py
```

### 2. Test Subscription Flow
1. Create a test patient user
2. Create test packages
3. Test subscription creation
4. Test payment processing
5. Test webhook handling

### 3. Production Checklist
- [ ] Update environment variables for production
- [ ] Set `PESAPAL_SANDBOX=False`
- [ ] Configure production domain URLs
- [ ] Register production IPN URL
- [ ] Set up monitoring for payment webhooks
- [ ] Configure backup payment status sync (cron job)

## Security Considerations

### 1. IPN Verification
The system verifies all IPN notifications by checking payment status with Pesapal before updating records.

### 2. Authentication
- All subscription endpoints require JWT authentication
- IPN endpoints are public but verify data with Pesapal
- Payment callbacks include order tracking ID verification

### 3. Data Protection
- No card details are stored in the system
- All sensitive operations are logged
- Payment gateway responses are stored for audit

## Monitoring and Maintenance

### 1. Regular Tasks
- Run subscription expiration check daily
- Sync payment status weekly
- Monitor IPN webhook delivery
- Check for failed payments

### 2. Logging
The system logs all Pesapal API interactions and subscription changes for debugging and audit purposes.

### 3. Error Handling
- Graceful handling of Pesapal API failures
- Retry mechanisms for authentication
- Fallback for webhook delivery failures

## Support and Troubleshooting

### Common Issues

#### 1. Authentication Failures
- Check consumer key and secret
- Verify environment (sandbox vs production)
- Check network connectivity

#### 2. Payment Status Not Updating
- Check IPN URL registration
- Verify webhook endpoint accessibility
- Run manual payment sync

#### 3. Subscription Not Activating
- Check payment status
- Verify webhook processing
- Check subscription status manually

### Logs to Check
- Django application logs
- Pesapal API response logs
- Webhook delivery logs
- Payment processing logs

For additional support, refer to the Pesapal Developer Documentation at https://developer.pesapal.com/