# OTP Verification System Guide

This guide explains how the OTP (One-Time Password) verification system works in the BluBus Pulse application.

## Overview

The OTP verification system provides secure authentication through temporary codes sent via email or WhatsApp. It's designed for user registration, login, and other sensitive operations.

## Features

- ✅ **Multi-channel delivery**: Email and WhatsApp support
- ✅ **Secure generation**: 6-digit random OTP codes
- ✅ **Time-limited**: 5-minute expiration
- ✅ **Attempt limiting**: Maximum 3 verification attempts
- ✅ **Single-use**: OTPs become invalid after successful verification
- ✅ **Rate limiting**: Prevents spam and abuse
- ✅ **Purpose-specific**: Different OTPs for registration, login, etc.

## API Endpoints

### 1. Send OTP

**Endpoint**: `POST /auth/send-otp`

**Description**: Sends an OTP code to the specified contact (email or phone).

**Request Body**:
```json
{
  "contact": "user@example.com",
  "contact_type": "email",
  "purpose": "registration"
}
```

**Parameters**:
- `contact` (string): Email address or phone number
- `contact_type` (enum): "email" or "whatsapp"
- `purpose` (string): Purpose of OTP (e.g., "registration", "login", "password_reset")

**Success Response**:
```json
{
  "status": "success",
  "code": 200,
  "data": null,
  "meta": {
    "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

**Error Response**:
```json
{
  "status": "error",
  "code": 429,
  "message": "Too many OTP requests. Try again in 3 minutes",
  "meta": {
    "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

### 2. Verify OTP (Registration)

**Endpoint**: `POST /auth/verify-otp/registration`

**Description**: Verifies an OTP code for user registration.

**Request Body**:
```json
{
  "contact": "user@example.com",
  "contact_type": "email",
  "otp": "123456",
  "purpose": "registration"
}
```

**Parameters**:
- `contact` (string): Email address or phone number
- `contact_type` (enum): "email" or "whatsapp"
- `otp` (string): 6-digit OTP code
- `purpose` (string): Purpose of OTP

**Success Response**:
```json
{
  "status": "success",
  "code": 200,
  "data": {
    "id": "user-uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_email_verified": true,
    "is_active": true,
    "created_at": "2024-01-01T10:00:00Z"
  },
  "meta": {
    "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

**Error Response**:
```json
{
  "status": "error",
  "code": 400,
  "message": "Invalid or expired OTP",
  "meta": {
    "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

### 3. Login with OTP

**Endpoint**: `POST /auth/login/otp`

**Description**: Authenticates user using OTP code.

**Request Body**:
```json
{
  "contact": "user@example.com",
  "contact_type": "email",
  "otp": "123456"
}
```

**Response**:
```json
{
  "success": true,
  "status": 200,
  "message": "Login successful",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

## Usage Examples

### Python Example

```python
import httpx
import asyncio

async def send_and_verify_otp():
    async with httpx.AsyncClient() as client:
        # 1. Send OTP
        send_response = await client.post(
            "http://localhost:8000/auth/send-otp",
            json={
                "contact": "user@example.com",
                "contact_type": "email",
                "purpose": "registration"
            }
        )
        
        if send_response.status_code == 200:
            print("OTP sent successfully")
            
            # 2. Verify OTP (user would enter the actual OTP)
            verify_response = await client.post(
                "http://localhost:8000/auth/verify-otp/registration",
                json={
                    "contact": "user@example.com",
                    "contact_type": "email",
                    "otp": "123456",  # User enters actual OTP
                    "purpose": "registration"
                }
            )
            
            if verify_response.status_code == 200:
                print("OTP verified successfully")
            else:
                print("OTP verification failed")
        else:
            print("Failed to send OTP")

# Run the example
asyncio.run(send_and_verify_otp())
```

### cURL Examples

#### Send OTP via Email
```bash
curl -X POST "http://localhost:8000/auth/send-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "contact": "user@example.com",
    "contact_type": "email",
    "purpose": "registration"
  }'
```

#### Send OTP via WhatsApp
```bash
curl -X POST "http://localhost:8000/auth/send-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "contact": "+919876543210",
    "contact_type": "whatsapp",
    "purpose": "registration"
  }'
```

#### Verify OTP
```bash
curl -X POST "http://localhost:8000/auth/verify-otp/registration" \
  -H "Content-Type: application/json" \
  -d '{
    "contact": "user@example.com",
    "contact_type": "email",
    "otp": "123456",
    "purpose": "registration"
  }'
```

#### Login with OTP
```bash
curl -X POST "http://localhost:8000/auth/login/otp" \
  -H "Content-Type: application/json" \
  -d '{
    "contact": "user@example.com",
    "contact_type": "email",
    "otp": "123456"
  }'
```

## Error Handling

### Common Error Responses

#### Invalid Contact Type
```json
{
  "detail": "Invalid contact type"
}
```

#### Invalid Email Format
```json
{
  "detail": [
    {
      "loc": ["body", "contact"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### OTP Not Found
```json
{
  "detail": "No OTP record found for user@example.com"
}
```

#### OTP Expired
```json
{
  "detail": "OTP expired for user@example.com"
}
```

#### OTP Already Used
```json
{
  "detail": "OTP already used for user@example.com"
}
```

#### Max Attempts Exceeded
```json
{
  "detail": "Max attempts exceeded for user@example.com"
}
```

#### Invalid OTP Code
```json
{
  "detail": "Invalid OTP for user@example.com"
}
```

#### Rate Limited
```json
{
  "detail": "Too many requests. Please try again later."
}
```

## Security Features

### 1. OTP Generation
- 6-digit random numeric codes
- Cryptographically secure random generation
- No predictable patterns

### 2. Expiration
- OTPs expire after 5 minutes
- Automatic cleanup of expired records
- No verification possible after expiration

### 3. Attempt Limiting
- Maximum 3 verification attempts per OTP
- Automatic invalidation after max attempts
- Prevents brute force attacks

### 4. Single Use
- OTPs become invalid after successful verification
- Cannot be reused even if not expired
- Prevents replay attacks

### 5. Rate Limiting
- Limits OTP requests per contact
- Prevents spam and abuse
- Configurable limits per time window

### 6. Purpose Validation
- OTPs are tied to specific purposes
- Registration OTPs cannot be used for login
- Prevents cross-purpose attacks

## Database Schema

### OTPRecord Table
```sql
CREATE TABLE otp_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contact VARCHAR(255) NOT NULL,
    contact_type contact_type_enum NOT NULL,
    otp_code VARCHAR(10) NOT NULL,
    purpose VARCHAR(50) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Configuration

### Environment Variables
```bash
# Email Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
SES_FROM_EMAIL=noreply@yourdomain.com

# WhatsApp Configuration
WA_API_URL=https://graph.facebook.com/v22.0
WA_API_TOKEN=your_whatsapp_token
WA_PHONE_NUMBER_ID=your_phone_number_id

# OTP Configuration
OTP_LENGTH=6
OTP_EXPIRY_MINUTES=5
OTP_MAX_ATTEMPTS=3
```

## Testing

### Running the Demo
```bash
# Start the server
python run.py

# Run the demo script
python otp_verification_demo.py

# Run the test suite
python test_otp_verification.py
```

### Test Scenarios
1. **Valid OTP Flow**: Send OTP → Verify with correct code
2. **Invalid OTP**: Send OTP → Verify with wrong code
3. **Expired OTP**: Send OTP → Wait for expiration → Verify
4. **Multiple Attempts**: Send OTP → Try wrong code multiple times
5. **Rate Limiting**: Send multiple OTPs quickly
6. **Cross-purpose**: Use registration OTP for login

## Best Practices

### For Developers
1. **Always validate input**: Check contact format and type
2. **Handle errors gracefully**: Provide clear error messages
3. **Implement rate limiting**: Prevent abuse
4. **Log security events**: Track failed attempts
5. **Use HTTPS**: Protect OTP transmission

### For Users
1. **Check spam folder**: Email OTPs might be filtered
2. **Enter OTP quickly**: Codes expire in 5 minutes
3. **Don't share OTPs**: Keep codes confidential
4. **Use correct contact**: Ensure contact info is accurate

## Troubleshooting

### Common Issues

#### OTP Not Received
- Check spam/junk folder for emails
- Verify phone number format for WhatsApp
- Check server logs for delivery errors
- Ensure proper API credentials

#### OTP Verification Fails
- Verify OTP code is correct
- Check if OTP has expired (5 minutes)
- Ensure OTP hasn't been used already
- Check attempt limit (max 3 tries)

#### Rate Limiting
- Wait before sending another OTP
- Check rate limit configuration
- Implement exponential backoff

#### Server Errors
- Check database connectivity
- Verify API credentials
- Check server logs for errors
- Ensure all services are running

## Support

For technical support or questions about the OTP verification system:

1. Check the server logs for detailed error messages
2. Review the API documentation
3. Test with the provided demo scripts
4. Contact the development team

---

*Last updated: December 2024*
