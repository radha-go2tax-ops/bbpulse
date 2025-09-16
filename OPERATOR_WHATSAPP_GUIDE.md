# Operator Registration Guide

This guide explains the operator registration functionality using OTP verification via WhatsApp or Email.

## Overview

The system provides a complete operator registration flow using OTP verification via WhatsApp or Email, allowing bus operators to register their companies through a secure, flexible approach that supports both mobile and email-based verification.

## Features

### 1. Operator Registration with OTP (WhatsApp or Email)
- **Send OTP**: Send verification code to operator's WhatsApp number or email
- **Verify OTP**: Verify the code and create operator account
- **Dual Contact Support**: Supports both WhatsApp and Email verification
- **Rate Limiting**: Prevents spam and abuse
- **Duplicate Prevention**: Checks for existing operators

### 2. Operator Listing
- **Public Listing**: List active operators (no authentication required)
- **Admin Listing**: List all operators with admin authentication
- **Search Functionality**: Search by company name, phone, email, city, state
- **Filtering**: Filter by status (PENDING, ACTIVE, SUSPENDED, REJECTED)

### 3. Operator Management
- **View Details**: Get specific operator information
- **Update Information**: Modify operator details
- **Status Management**: Activate, suspend, or reject operators

## API Endpoints

### 1. Send OTP (Common Endpoint)
```http
POST /auth/send-otp
Content-Type: application/json

# For WhatsApp
{
  "contact": "+919876543210",
  "contact_type": "whatsapp",
  "purpose": "operator_registration"
}

# For Email
{
  "contact": "test@example.com",
  "contact_type": "email",
  "purpose": "operator_registration"
}
```

**Success Response:**
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

**Error Response:**
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


### 2. Verify OTP (Common Endpoint)
```http
POST /auth/verify-otp
Content-Type: application/json

# For WhatsApp
{
  "contact": "+919876543210",
  "contact_type": "whatsapp",
  "otp": "123456",
  "purpose": "registration"
}

# For Email
{
  "contact": "test@example.com",
  "contact_type": "email",
  "otp": "123456",
  "purpose": "registration"
}
```

### 3. Register Operator
```http
POST /operators/register
Content-Type: application/json

# For WhatsApp Registration
{
  "contact": "+919876543210",
  "contact_type": "whatsapp",
  "otp": "123456",
  "registration_data": {
    "company_name": "Test Bus Company",
    "contact_phone": "+919876543210",
    "business_license": "BL123456789",
    "address": "123 Test Street, Test City",
    "city": "Mumbai",
    "state": "Maharashtra",
    "country": "India",
    "postal_code": "400001"
  }
}

# For Email Registration
{
  "contact": "test@example.com",
  "contact_type": "email",
  "otp": "123456",
  "registration_data": {
    "company_name": "Test Bus Company",
    "contact_phone": "+919876543211",
    "business_license": "BL123456790",
    "address": "456 Test Avenue, Test City",
    "city": "Delhi",
    "state": "Delhi",
    "country": "India",
    "postal_code": "110001"
  }
}
```

**Success Response:**
```json
{
  "status": "success",
  "code": 201,
  "data": {
    "operator": {
      "id": 1,
      "company_name": "Test Bus Company",
      "contact_email": "operator_+919876543210@temp.com",
      "contact_phone": "+919876543210",
      "business_license": "BL123456789",
      "address": "123 Test Street, Test City",
      "city": "Mumbai",
      "state": "Maharashtra",
      "country": "India",
      "postal_code": "400001",
      "status": "PENDING",
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z"
    },
    "login_credentials": {
      "email": "operator_+919876543210@temp.com",
      "mobile": "+919876543210",
      "temporary_password": "TempPass1123!",
      "message": "Please change your password after first login. You can use email or mobile for OTP login."
    }
  },
  "meta": {
    "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

**Error Response:**
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

### 3. List Operators (Public)
```http
GET /operators/public?search=Mumbai&status=ACTIVE&skip=0&limit=50
```

**Response:**
```json
[
  {
    "id": 1,
    "company_name": "Test Bus Company",
    "contact_email": "operator_+919876543210@temp.com",
    "contact_phone": "+919876543210",
    "status": "ACTIVE",
    "city": "Mumbai",
    "state": "Maharashtra",
    "created_at": "2024-01-01T10:00:00Z"
  }
]
```

### 4. List Operators (Admin)
```http
GET /operators/?search=Test&status=PENDING&skip=0&limit=100
Authorization: Bearer <admin_token>
```

### 5. Get Operator Details
```http
GET /operators/{operator_id}
Authorization: Bearer <token>
```

## Registration Flow

### Step 1: Send OTP
1. Operator provides their WhatsApp number
2. System validates phone number format
3. Checks for existing operators with same phone
4. Sends OTP via WhatsApp using Facebook Graph API
5. Stores OTP in database with 5-minute expiry

### Step 2: Verify OTP and Register
1. Operator enters OTP received on WhatsApp
2. System verifies OTP against stored record
3. Checks for expiry and attempt limits
4. Creates operator account with PENDING status
5. Sends notification about account creation

### Step 3: Complete Profile
1. Operator can update their profile
2. Add proper email address
3. Upload required documents
4. Admin reviews and activates account

## Security Features

### Rate Limiting
- OTP requests: Limited per phone number
- Registration attempts: Limited per phone number
- Login attempts: Limited per user

### OTP Security
- 6-digit numeric OTP
- 5-minute expiry
- Maximum 3 verification attempts
- One-time use only

### Data Validation
- Phone number format validation
- Business license format validation
- Required field validation
- Duplicate prevention

## Configuration

### WhatsApp API Settings
```env
WA_API_URL=https://graph.facebook.com/v22.0
WA_API_TOKEN=your_facebook_token
WA_PHONE_NUMBER_ID=your_phone_number_id
```

### OTP Settings
```python
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5
MAX_ATTEMPTS = 3
```

## Testing

### Manual Testing
1. Start the server: `uvicorn bbpulse.main:app --reload`
2. Run test script: `python test_operator_whatsapp_flow.py`
3. Follow the interactive prompts

### Test Data
```json
{
  "company_name": "Test Bus Company",
  "contact_phone": "+919876543210",
  "business_license": "BL123456789",
  "address": "123 Test Street, Test City",
  "city": "Mumbai",
  "state": "Maharashtra",
  "country": "India",
  "postal_code": "400001"
}
```

## Error Handling

### Common Errors
- **400 Bad Request**: Invalid phone format, duplicate operator, invalid OTP
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: WhatsApp API failure, database error

### Error Response Format
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Database Schema

### Operators Table
- `id`: Primary key
- `company_name`: Company name
- `contact_email`: Contact email (temporary for WhatsApp registration)
- `contact_phone`: WhatsApp phone number
- `business_license`: Business license number
- `address`: Company address
- `city`, `state`, `country`, `postal_code`: Location details
- `status`: PENDING, ACTIVE, SUSPENDED, REJECTED
- `created_at`, `updated_at`: Timestamps

### OTP Records Table
- `id`: Primary key (UUID)
- `contact`: Phone number or email
- `contact_type`: EMAIL or WHATSAPP
- `otp_code`: 6-digit OTP
- `purpose`: registration, login, password_reset
- `expires_at`: Expiry timestamp
- `is_used`: Boolean flag
- `attempts`: Number of verification attempts

## Next Steps

1. **Email Verification**: Add email verification for complete profile
2. **Document Upload**: Implement document upload functionality
3. **Admin Dashboard**: Create admin interface for operator management
4. **Notifications**: Add email/SMS notifications for status changes
5. **Analytics**: Track registration metrics and success rates

## Support

For issues or questions:
1. Check the API documentation at `/docs`
2. Review the test script for examples
3. Check server logs for detailed error messages
4. Verify WhatsApp API configuration
