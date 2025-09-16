# Complete Operator Registration to Listing Flow Guide

This comprehensive guide walks you through the entire process from operator registration to listing operators in the BBPulse system.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Step 1: Start the Application](#step-1-start-the-application)
3. [Step 2: Send OTP for Registration](#step-2-send-otp-for-registration)
4. [Step 3: Register Operator](#step-3-register-operator)
5. [Step 4: List Operators (Public)](#step-4-list-operators-public)
6. [Step 5: Admin Authentication](#step-5-admin-authentication)
7. [Step 6: List Operators (Admin)](#step-6-list-operators-admin)
8. [Step 7: Get Specific Operator Details](#step-7-get-specific-operator-details)
9. [Step 8: Update Operator Status](#step-8-update-operator-status)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.8+ installed
- Virtual environment activated
- Database configured (SQLite/PostgreSQL)
- Required dependencies installed

## Step 1: Start the Application

```bash
# Navigate to project directory
cd C:\Users\Tanuja\OneDrive\Documents\bbpulse

# Activate virtual environment
venv\Scripts\activate

# Start the FastAPI server
python -m uvicorn bbpulse.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Verify Application:**
- Open browser: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

## Step 2: Send OTP for Registration

Before registering an operator, you need to send an OTP to verify their contact (WhatsApp or Email).

### 2.1 Send OTP via WhatsApp

```bash
curl -X POST "http://localhost:8000/auth/send-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "contact": "+919876543210",
    "contact_type": "whatsapp",
    "purpose": "operator_registration"
  }'
```

### 2.2 Send OTP via Email

```bash
curl -X POST "http://localhost:8000/auth/send-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "contact": "operator@example.com",
    "contact_type": "email",
    "purpose": "operator_registration"
  }'
```

**Expected Success Response:**
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

**Rate Limiting Response:**
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

## Step 3: Register Operator

After receiving the OTP, use it to register the operator.

### 3.1 Register via WhatsApp

```bash
curl -X POST "http://localhost:8000/operators/register" \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

### 3.2 Register via Email

```bash
curl -X POST "http://localhost:8000/operators/register" \
  -H "Content-Type: application/json" \
  -d '{
    "contact": "operator@example.com",
    "contact_type": "email",
    "otp": "123456",
    "registration_data": {
      "company_name": "Delhi Transport Co",
      "contact_phone": "+919876543211",
      "business_license": "BL123456790",
      "address": "456 Test Avenue, Test City",
      "city": "Delhi",
      "state": "Delhi",
      "country": "India",
      "postal_code": "110001"
    }
  }'
```

**Expected Success Response:**
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

**Error Response (Invalid OTP):**
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

## Step 4: List Operators (Public)

Now you can list operators. The public endpoint doesn't require authentication.

### 4.1 List All Active Operators

```bash
curl -X GET "http://localhost:8000/operators/public"
```

### 4.2 Search Operators by Location

```bash
curl -X GET "http://localhost:8000/operators/public?search=Mumbai&status=ACTIVE&skip=0&limit=20"
```

### 4.3 Paginated Results

```bash
curl -X GET "http://localhost:8000/operators/public?skip=0&limit=10"
```

**Expected Response:**
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

## Step 5: Admin Authentication

To access admin features, you need to authenticate as an operator user.

### 5.1 Login with Password (Using Generated Credentials)

```bash
curl -X POST "http://localhost:8000/auth/login/password" \
  -H "Content-Type: application/json" \
  -d '{
    "contact": "operator_+919876543210@temp.com",
    "contact_type": "email",
    "password": "TempPass1123!"
  }'
```

### 5.2 Login with OTP

First, send OTP for login:
```bash
curl -X POST "http://localhost:8000/auth/send-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "contact": "operator_+919876543210@temp.com",
    "contact_type": "email",
    "purpose": "login"
  }'
```

Then verify OTP:
```bash
curl -X POST "http://localhost:8000/auth/login/otp" \
  -H "Content-Type: application/json" \
  -d '{
    "contact": "operator_+919876543210@temp.com",
    "contact_type": "email",
    "otp": "123456"
  }'
```

**Expected Success Response:**
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

## Step 6: List Operators (Admin)

With authentication, you can access the full operator listing with more details.

### 6.1 List All Operators (Authenticated)

```bash
curl -X GET "http://localhost:8000/operators/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 6.2 Search and Filter Operators

```bash
curl -X GET "http://localhost:8000/operators/?search=Test&status=PENDING&skip=0&limit=100" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected Response:**
```json
[
  {
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
    "verification_notes": null,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z",
    "verified_at": null,
    "documents": [],
    "users": []
  }
]
```

## Step 7: Get Specific Operator Details

Get detailed information about a specific operator.

```bash
curl -X GET "http://localhost:8000/operators/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected Response:**
```json
{
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
  "verification_notes": null,
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z",
  "verified_at": null,
  "documents": [],
  "users": []
}
```

## Step 8: Update Operator Status

As an admin, you can update operator status.

### 8.1 Activate Operator

```bash
curl -X POST "http://localhost:8000/operators/1/activate" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 8.2 Suspend Operator

```bash
curl -X POST "http://localhost:8000/operators/1/suspend" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Document verification pending"
  }'
```

### 8.3 Update Operator Information

```bash
curl -X PUT "http://localhost:8000/operators/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Updated Mumbai Bus Services",
    "status": "ACTIVE",
    "verification_notes": "All documents verified"
  }'
```

## Complete Flow Example

Here's a complete example that demonstrates the entire flow:

```bash
#!/bin/bash

# Step 1: Start the application (run this in a separate terminal)
# python -m uvicorn bbpulse.main:app --reload --host 0.0.0.0 --port 8000

# Step 2: Send OTP for registration
echo "Step 2: Sending OTP for registration..."
OTP_RESPONSE=$(curl -s -X POST "http://localhost:8000/auth/send-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "contact": "+919876543210",
    "contact_type": "whatsapp",
    "purpose": "operator_registration"
  }')

echo "OTP Response: $OTP_RESPONSE"

# Step 3: Register operator (replace 123456 with actual OTP)
echo "Step 3: Registering operator..."
REGISTER_RESPONSE=$(curl -s -X POST "http://localhost:8000/operators/register" \
  -H "Content-Type: application/json" \
  -d '{
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
  }')

echo "Registration Response: $REGISTER_RESPONSE"

# Step 4: List operators (public)
echo "Step 4: Listing operators (public)..."
PUBLIC_LIST=$(curl -s -X GET "http://localhost:8000/operators/public")
echo "Public List: $PUBLIC_LIST"

# Step 5: Login to get token
echo "Step 5: Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/auth/login/password" \
  -H "Content-Type: application/json" \
  -d '{
    "contact": "operator_+919876543210@temp.com",
    "contact_type": "email",
    "password": "TempPass1123!"
  }')

echo "Login Response: $LOGIN_RESPONSE"

# Extract token (you would need to parse JSON in a real script)
# TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.data.access_token')

# Step 6: List operators (authenticated)
echo "Step 6: Listing operators (authenticated)..."
# ADMIN_LIST=$(curl -s -X GET "http://localhost:8000/operators/" \
#   -H "Authorization: Bearer $TOKEN")
# echo "Admin List: $ADMIN_LIST"

echo "Complete flow executed!"
```

## Troubleshooting

### Common Issues

1. **OTP Not Received**
   - Check rate limiting (max 3 requests per 5 minutes)
   - Verify contact format
   - Check email/WhatsApp service configuration

2. **Invalid OTP Error**
   - OTP expires in 5 minutes
   - Maximum 3 attempts allowed
   - Check if OTP was already used

3. **Authentication Failed**
   - Verify token format
   - Check token expiration (30 minutes)
   - Ensure proper Authorization header

4. **Database Errors**
   - Check database connection
   - Verify tables are created
   - Check for constraint violations

### Debug Commands

```bash
# Check application health
curl -X GET "http://localhost:8000/health"

# Check database status
curl -X GET "http://localhost:8000/health/database"

# View API documentation
# Open: http://localhost:8000/docs
```

### Logs

Check application logs for detailed error information:
- Look for ERROR level messages
- Check OTP service logs
- Verify database connection logs

## Next Steps

After completing this flow, you can:

1. **Upload Documents**: Use the document management endpoints
2. **Manage Users**: Create additional operator users
3. **Set Up Notifications**: Configure email/WhatsApp notifications
4. **Monitor System**: Use health check endpoints
5. **Scale**: Configure for production deployment

## API Reference

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

This guide provides a complete walkthrough from operator registration to listing. Each step includes practical examples and expected responses to help you understand and implement the system effectively.
