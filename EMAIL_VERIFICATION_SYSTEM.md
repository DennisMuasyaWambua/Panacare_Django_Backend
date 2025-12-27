# New Email Verification System

## Overview

The Panacare email verification system has been completely redesigned based on the working implementation from the Bionexus project. This new system uses 6-digit verification codes instead of complex URL-based activation links.

## Key Features

### 1. Simple 6-Digit Codes
- Users receive a 6-digit numeric code instead of long activation URLs
- Codes expire in 15 minutes for security
- Easy to type on mobile devices and user-friendly

### 2. Robust Email Sending
- Asynchronous email sending prevents worker timeouts
- Background thread processing with proper error handling
- Network timeout protection (30 seconds)
- Graceful fallback when email sending fails

### 3. Security Features
- Previous unused codes are automatically invalidated when new ones are generated
- Expiration tracking with timezone awareness
- Proper validation of codes before activation

## API Endpoints

### 1. User Registration
**POST** `/api/users/register/`

```json
{
  "username": "user123",
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "role": "community_health_provider"
}
```

**Response:**
```json
{
  "detail": "Registration successful. A verification email with a 6-digit code is being sent to your email address. Please check your email (including spam folder) for the verification code.",
  "user": { ... }
}
```

### 2. Email Verification
**POST** `/api/users/verify-email/`

```json
{
  "email": "user@example.com",
  "verification_code": "123456"
}
```

**Response:**
```json
{
  "detail": "Email verified successfully!",
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
}
```

### 3. Resend Verification Code
**POST** `/api/users/resend-verification/`

```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "A new verification email with 6-digit code has been sent to your email address"
}
```

## Database Schema

### EmailVerification Model

```python
class EmailVerification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verifications')
    verification_code = models.CharField(max_length=6)  # 6-digit code
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # 15 minutes from creation
    is_used = models.BooleanField(default=False)
```

## Email Template

The system sends clean, simple email messages:

```
Subject: Verify your Panacare account

Hello John,

Thank you for registering with Panacare!

Your verification code is: 123456

This code will expire in 15 minutes.

Please use this code to verify your email address and activate your account.

Best regards,
Panacare Team
```

## Benefits Over Previous System

### 1. **Reliability**
- No more 502 timeout errors
- Async processing prevents blocking
- Better error handling and logging

### 2. **User Experience** 
- Simple 6-digit codes are easier to use
- Works well on mobile devices
- Clear, readable email messages

### 3. **Security**
- Short expiration time (15 minutes)
- Automatic invalidation of old codes
- Proper validation and error handling

### 4. **Maintenance**
- Based on proven working implementation (Bionexus)
- Cleaner code structure
- Better separation of concerns

## Migration Guide

### For Existing Users
1. Run the migration: `python manage.py migrate users`
2. Update frontend to use new verification endpoint
3. Test email sending in development

### For Frontend Integration
1. Change registration flow to expect 6-digit codes
2. Update verification form to accept 6-digit input
3. Use new API endpoints for verification and resending

### For Production Deployment
1. Ensure email settings are configured in Railway environment variables
2. Test email delivery before going live
3. Monitor logs for email sending success/failure

## Configuration

### Environment Variables
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=noreply@panacare.com
EMAIL_TIMEOUT=30
```

### For Railway Deployment
Set these in Railway's environment variables instead of .env file for security.

## Testing

### Development Testing
```python
# Set console backend for development
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Production Testing
1. Register a test user
2. Check email delivery
3. Verify the 6-digit code works
4. Test code expiration
5. Test resend functionality

## Troubleshooting

### Common Issues

1. **Network Unreachable (Errno 101)**
   - This is a Railway/hosting platform issue
   - Consider using SendGrid or other email services
   - Check firewall settings

2. **Email Not Received**
   - Check spam/junk folder
   - Verify email credentials are correct
   - Check email sending logs

3. **Code Expired**
   - Codes expire in 15 minutes
   - Use resend endpoint to get new code

4. **Invalid Code**
   - Check for typos in 6-digit code
   - Ensure using the most recent code (old ones are invalidated)

## Files Modified

1. **models.py** - Added EmailVerification model, updated User.send_verification_email()
2. **serializers.py** - Added EmailVerificationSerializer, ResendVerificationSerializer
3. **views.py** - Updated EmailVerifyAPIView, ResendVerificationAPIView
4. **urls.py** - Updated URL patterns
5. **settings.py** - Added EMAIL_TIMEOUT setting

This new system provides a much more reliable and user-friendly email verification experience.