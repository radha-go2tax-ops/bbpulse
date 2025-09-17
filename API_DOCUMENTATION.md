# BluBus Pulse API Documentation

This document provides comprehensive API documentation for the BluBus Pulse application, including detailed request/response examples for all OTP and operator registration endpoints.

## Table of Contents

1. [Authentication Endpoints](#authentication-endpoints)
2. [Operator Management Endpoints](#operator-management-endpoints)
3. [Response Format Standards](#response-format-standards)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Testing](#testing)

## Authentication Endpoints

### 1. User Registration

**Endpoint:** `POST /auth/register`

**Description:** Register a new user with OTP verification.

**Request Body:**
```json
{
  "contact": "user@example.com",
  "contact_type": "email",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Success Response (201):**
```json
{
  "status": "success",
  "code": 201,
  "data": {
    "id": "uuid-string",
    "email": "user@example.com",
    "mobile": null,
    "full_name": "John Doe",
    "source": "email",
    "is_active": true,
    "is_email_verified": false,
    "is_mobile_verified": false,
    "login_attempts": 0,
    "last_login": null,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z"
  },
  "meta": {
    "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

**Error Response (400):**
```json
{
  "status": "error",
  "code": 400,
  "message": "Validation failed",
  "errors": [
    {
      "field": "password",
      "issue": "Must be at least 8 characters"
    }
  ],
  "meta": {
    "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

### 2. Send OTP

**Endpoint:** `POST /auth/send-otp`

**Description:** Send a 6-digit OTP to the specified contact for various purposes.

**Request Body:**
```json
{
  "contact": "user@example.com",
  "contact_type": "email",
  "purpose": "registration"
}
```

**Purpose Options:**
- `"registration"` - For user registration verification
- `"login"` - For OTP-based login
- `"password_update"` - For password reset/change operations

**Example Requests:**
```json
// For registration
{
  "contact": "user@example.com",
  "contact_type": "email",
  "purpose": "registration"
}

// For login
{
  "contact": "user@example.com",
  "contact_type": "email",
  "purpose": "login"
}

// For password update (forgot password or change password)
{
  "contact": "user@example.com",
  "contact_type": "email",
  "purpose": "password_update"
}
```

**Success Response (200):**
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

**Error Response (429):**
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

### 3. Verify OTP

**Endpoint:** `POST /auth/verify-otp`

**Description:** Verify OTP for registration or login.

**Request Body:**
```json
{
  "contact": "user@example.com",
  "contact_type": "email",
  "otp": "123456",
  "purpose": "registration"
}
```

**Success Response (200):**
```json
{
  "status": "success",
  "code": 200,
  "data": {
    "id": "uuid-string",
    "email": "user@example.com",
    "mobile": null,
    "full_name": "John Doe",
    "source": "email",
    "is_active": true,
    "is_email_verified": true,
    "is_mobile_verified": false,
    "login_attempts": 0,
    "last_login": null,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z"
  },
  "meta": {
    "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

### 4. Update Password

**Endpoint:** `POST /auth/update-password`

**Description:** Update password using OTP verification. Works for both password reset (forgot password) and password change scenarios. Supports both regular users and operator users.

**Prerequisites:** First call `/auth/send-otp` with `purpose="password_update"` to receive OTP.

**Request Body:**
```json
{
  "contact": "user@example.com",
  "contact_type": "email",
  "otp": "123456",
  "new_password": "NewSecurePass123!"
}
```

**Success Response (200):**
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

**Error Response (400):**
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

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

### 5. OTP Login

**Endpoint:** `POST /auth/login/otp`

**Description:** Authenticate user with OTP. Supports both regular users and operator users with email or mobile OTP.

**Request Body:**
```json
{
  "contact": "user@example.com",
  "contact_type": "email",
  "otp": "123456"
}
```

**Alternative Request (Mobile OTP):**
```json
{
  "contact": "+919876543210",
  "contact_type": "whatsapp",
  "otp": "123456"
}
```

**Success Response (200):**
```json
{
  "status": "success",
  "code": 200,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 1800
  },
  "meta": {
    "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

## Operator Management Endpoints

### 1. Register Operator

**Endpoint:** `POST /operators/register`

**Description:** Register a new bus operator with OTP verification.

**Request Body:**
```json
{
  "contact": "+919876543210",
  "contact_type": "whatsapp",
  "otp": "123456",
  "registration_data": {
    "company_name": "Mumbai Bus Services",
    "contact_phone": "+919876543210",
    "business_license": "BL123456789",
    "address": "123 Main Street, Andheri",
    "city": "Mumbai",
    "state": "Maharashtra",
    "country": "India",
    "postal_code": "400001"
  }
}
```

**Success Response (201):**
```json
{
  "status": "success",
  "code": 201,
  "data": {
    "operator": {
      "id": 1,
      "company_name": "Mumbai Bus Services",
      "contact_email": "operator_+919876543210@temp.com",
      "contact_phone": "+919876543210",
      "business_license": "BL123456789",
      "address": "123 Main Street, Andheri",
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

**Error Response (400):**
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

### 2. List Operators (Public)

**Endpoint:** `GET /operators/public`

**Description:** List active operators (public access).

**Query Parameters:**
- `skip` (integer, optional): Number of records to skip (default: 0)
- `limit` (integer, optional): Maximum records to return (default: 50, max: 100)
- `status` (string, optional): Filter by status (default: "ACTIVE")
- `search` (string, optional): Search by company name, city, or state

**Example Request:**
```
GET /operators/public?search=Mumbai&status=ACTIVE&skip=0&limit=20
```

**Success Response (200):**
```json
[
  {
    "id": 1,
    "company_name": "Mumbai Bus Services",
    "contact_phone": "+919876543210",
    "status": "ACTIVE",
    "city": "Mumbai",
    "state": "Maharashtra",
    "created_at": "2024-01-01T10:00:00Z"
  },
  {
    "id": 2,
    "company_name": "Delhi Transport Co",
    "contact_phone": "+919876543211",
    "status": "ACTIVE",
    "city": "Delhi",
    "state": "Delhi",
    "created_at": "2024-01-01T11:00:00Z"
  }
]
```

### 3. Create Operator User

**Endpoint:** `POST /operators/{operator_id}/users`

**Description:** Create a new user for an operator (admin only). Supports both email and mobile.

**Request Body:**
```json
{
  "email": "admin@company.com",
  "mobile": "+919876543210",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "role": "ADMIN"
}
```

**Success Response (201):**
```json
{
  "status": "success",
  "code": 201,
  "data": {
    "id": 1,
    "operator_id": 1,
    "email": "admin@company.com",
    "mobile": "+919876543210",
    "first_name": "John",
    "last_name": "Doe",
    "role": "ADMIN",
    "is_active": true,
    "email_verified": false,
    "mobile_verified": false,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z"
  },
  "meta": {
    "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

**Error Response (400):**
```json
{
  "status": "error",
  "code": 400,
  "message": "User with this email already exists",
  "meta": {
    "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

### 4. List Operator Users

**Endpoint:** `GET /operators/{operator_id}/users`

**Description:** List all users for a specific operator.

**Query Parameters:**
- `skip` (integer, optional): Number of records to skip (default: 0)
- `limit` (integer, optional): Maximum records to return (default: 50, max: 100)
- `role` (string, optional): Filter by role (ADMIN, MANAGER, VIEWER)
- `is_active` (boolean, optional): Filter by active status

**Success Response (200):**
```json
{
  "status": "success",
  "code": 200,
  "data": [
    {
      "id": 1,
      "operator_id": 1,
      "email": "admin@company.com",
      "mobile": "+919876543210",
      "first_name": "John",
      "last_name": "Doe",
      "role": "ADMIN",
      "is_active": true,
      "email_verified": true,
      "mobile_verified": true,
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z"
    }
  ],
  "meta": {
    "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
    "timestamp": "2024-01-01T10:00:00Z",
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "total": 1
    }
  }
}
```

## Response Format Standards

All API responses follow a consistent format:

### Success Response
```json
{
  "status": "success",
  "code": 200,
  "data": { /* response data */ },
  "meta": {
    "requestId": "uuid-string",
    "timestamp": "2024-01-01T10:00:00Z",
    "pagination": { /* optional pagination info */ }
  }
}
```

### Error Response
```json
{
  "status": "error",
  "code": 400,
  "message": "Error description",
  "errors": [ /* optional field-specific errors */ ],
  "meta": {
    "requestId": "uuid-string",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

### List Response
```json
{
  "status": "success",
  "code": 200,
  "data": [ /* array of items */ ],
  "meta": {
    "requestId": "uuid-string",
    "timestamp": "2024-01-01T10:00:00Z",
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "total": 42
    }
  }
}
```

## Error Handling

### HTTP Status Codes

- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Access denied
- **404 Not Found**: Resource not found
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

### Error Response Fields

- `status`: Always "error" for error responses
- `code`: HTTP status code
- `message`: Human-readable error message
- `errors`: Array of field-specific validation errors (optional)
- `meta`: Request metadata including requestId and timestamp

### Common Error Scenarios

1. **Validation Errors (400)**:
   ```json
   {
     "status": "error",
     "code": 400,
     "message": "Validation failed",
     "errors": [
       {
         "field": "email",
         "issue": "Invalid email format"
       }
     ],
     "meta": { /* ... */ }
   }
   ```

2. **Authentication Errors (401)**:
   ```json
   {
     "status": "error",
     "code": 401,
     "message": "Authentication failed",
     "meta": { /* ... */ }
   }
   ```

3. **Rate Limit Errors (429)**:
   ```json
   {
     "status": "error",
     "code": 429,
     "message": "Too many requests. Try again in 3 minutes",
     "meta": { /* ... */ }
   }
   ```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **OTP Requests**: 3 requests per 5 minutes per contact
- **Registration Attempts**: 5 attempts per hour per contact
- **Login Attempts**: 10 attempts per hour per contact

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Time when limit resets

## Testing

### Test Script

Run the response consistency test:
```bash
python test_response_consistency.py
```

This script validates:
- ✅ Response format consistency across all endpoints
- ✅ Success response structure validation
- ✅ Error response structure validation
- ✅ Metadata validation (requestId, timestamp)
- ✅ Field validation and error handling

### Manual Testing

1. **Start the server**:
   ```bash
   uvicorn bbpulse.main:app --reload
   ```

2. **Access Swagger UI**:
   ```
   http://localhost:8000/docs
   ```

3. **Test endpoints** using the interactive documentation or tools like Postman/curl.

### Example cURL Commands

**Send OTP:**
```bash
curl -X POST "http://localhost:8000/auth/send-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "contact": "user@example.com",
    "contact_type": "email",
    "purpose": "registration"
  }'
```

**Register Operator:**
```bash
curl -X POST "http://localhost:8000/operators/register" \
  -H "Content-Type: application/json" \
  -d '{
    "contact": "+919876543210",
    "contact_type": "whatsapp",
    "otp": "123456",
    "registration_data": {
      "company_name": "Test Bus Company",
      "contact_phone": "+919876543210",
      "business_license": "BL123456789",
      "address": "123 Test Street",
      "city": "Mumbai",
      "state": "Maharashtra",
      "country": "India",
      "postal_code": "400001"
    }
  }'
```

## Contact Types

- `email`: Email address verification
- `whatsapp`: WhatsApp phone number verification

## OTP Purposes

- `registration`: User registration verification
- `login`: OTP-based user login
- `password_update`: Password reset/change operations (unified)
- `operator_registration`: Operator registration

## Security Features

- JWT token-based authentication
- OTP expiration (5 minutes)
- Rate limiting
- Input validation
- SQL injection prevention
- XSS protection
- CORS configuration

---

For more detailed information, see:
- [OTP Verification Guide](OTP_VERIFICATION_GUIDE.md)
- [Operator WhatsApp Guide](OPERATOR_WHATSAPP_GUIDE.md)
- [Registration System Guide](REGISTRATION_SYSTEM.md)
