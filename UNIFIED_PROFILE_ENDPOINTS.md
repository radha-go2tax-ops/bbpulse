# Unified Profile Endpoints Documentation

## Overview

The BluBus Pulse API now provides a unified profile management system that automatically detects user types and returns appropriate data. This eliminates the confusion between different profile endpoints and provides a consistent interface for both general users and operator users.

## Endpoint Architecture

### 1. Unified Endpoint (Recommended)
- **`GET /auth/profile`** - Automatically detects user type and returns appropriate profile data
- **`PUT /auth/profile`** - Updates profile based on detected user type

### 2. Type-Specific Endpoints (For Explicit Control)
- **`GET /auth/user-profile`** - Specifically for general users (passengers/end-users)
- **`GET /auth/operator-profile`** - Specifically for operator users (company employees)

## User Types

### General Users (`User` model)
- **Purpose**: Passengers and end-users who use the bus tracking service
- **Authentication**: Multi-channel (email/WhatsApp) with OTP verification
- **ID Type**: UUID
- **Key Fields**: `id`, `email`, `mobile`, `full_name`, `source`, `is_active`, `is_email_verified`, `is_mobile_verified`

### Operator Users (`OperatorUser` model)
- **Purpose**: Company employees who manage bus operations
- **Authentication**: Email/password with role-based access
- **ID Type**: Integer
- **Key Fields**: `id`, `email`, `mobile`, `first_name`, `last_name`, `role`, `operator_id`, `is_active`, `email_verified`, `mobile_verified`

## API Endpoints

### GET /auth/profile
**Unified profile endpoint that automatically detects user type**

```http
GET /auth/profile
Authorization: Bearer <your-token>
```

**Response for General User:**
```json
{
  "status": "success",
  "code": 200,
  "user_type": "user",
  "data": {
    "id": "uuid-string",
    "email": "user@example.com",
    "mobile": "+919876543210",
    "full_name": "John Doe",
    "source": "email",
    "is_active": true,
    "is_email_verified": true,
    "is_mobile_verified": false,
    "login_attempts": 0,
    "last_login": "2024-01-16T10:12:02.998989+05:30",
    "created_at": "2024-01-16T10:12:02.998989+05:30",
    "updated_at": "2024-01-16T10:12:02.998989+05:30"
  },
  "meta": {
    "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
    "timestamp": "2024-01-16T10:12:02.998989+05:30"
  }
}
```

**Response for Operator User:**
```json
{
  "status": "success",
  "code": 200,
  "user_type": "operator_user",
  "data": {
    "id": 8,
    "email": "admin@testcompany.com",
    "mobile": "+919876543210",
    "first_name": "Test",
    "last_name": "Admin",
    "role": "ADMIN",
    "operator_id": 12,
    "is_active": true,
    "email_verified": true,
    "mobile_verified": true,
    "last_login": "2024-01-16T10:12:02.998989+05:30",
    "created_at": "2024-01-16T10:12:02.998989+05:30",
    "updated_at": "2024-01-16T10:12:02.998989+05:30"
  },
  "meta": {
    "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
    "timestamp": "2024-01-16T10:12:02.998989+05:30"
  }
}
```

### GET /auth/user-profile
**Specific endpoint for general users only**

```http
GET /auth/user-profile
Authorization: Bearer <your-token>
```

**When to use:**
- When you specifically need profile data for general system users
- For passengers who registered through the public registration system
- When you know the user is not an operator employee

**Error Response (if operator user tries to access):**
```json
{
  "detail": "This endpoint is for general users only. Use /auth/operator-profile for operator users."
}
```

### GET /auth/operator-profile
**Specific endpoint for operator users only**

```http
GET /auth/operator-profile
Authorization: Bearer <your-token>
```

**When to use:**
- When you specifically need profile data for operator users
- For company employees who manage bus operations
- When you know the user is an operator employee

**Error Response (if general user tries to access):**
```json
{
  "detail": "This endpoint is for operator users only. Use /auth/user-profile for general users."
}
```

### PUT /auth/profile
**Unified profile update endpoint**

```http
PUT /auth/profile
Authorization: Bearer <your-token>
Content-Type: application/json

{
  "full_name": "John Smith",
  "email": "john.smith@example.com",
  "mobile": "+919876543210"
}
```

**Supported Updates:**
- **General users**: `full_name`, `email`, `mobile`
- **Operator users**: `full_name`, `email`, `mobile` (role and operator_id cannot be changed)

## When to Use Each Endpoint

### Use `/auth/profile` (Unified) when:
- ✅ You don't know the user type in advance
- ✅ You want a single endpoint that works for all users
- ✅ You're building a generic profile management interface
- ✅ You want to minimize API complexity

### Use `/auth/user-profile` when:
- ✅ You specifically need general user data
- ✅ You're building a passenger-facing application
- ✅ You want to ensure only general users can access the endpoint
- ✅ You need explicit type checking

### Use `/auth/operator-profile` when:
- ✅ You specifically need operator user data
- ✅ You're building an operator management interface
- ✅ You want to ensure only operator users can access the endpoint
- ✅ You need operator-specific fields like `role` and `operator_id`

## Migration Guide

### From Old Endpoints

**Old Endpoints (Deprecated):**
- `GET /auth/me` → Use `GET /auth/profile` or `GET /auth/operator-profile`
- `GET /auth/profile` → Use `GET /auth/profile` or `GET /auth/user-profile`

**Migration Steps:**
1. Update client code to use new endpoint names
2. Handle the new `user_type` field in responses
3. Update error handling for type-specific endpoints
4. Test with both user types

### Response Format Changes

**New Fields:**
- `user_type`: "user" or "operator_user" to identify the user type
- Consistent response structure across all endpoints

**Removed Fields:**
- No fields removed, but some fields are user-type specific

## Error Handling

### Common Error Responses

**401 Unauthorized:**
```json
{
  "status": "error",
  "code": 401,
  "message": "Could not validate credentials",
  "meta": {
    "requestId": "uuid-string",
    "timestamp": "2024-01-16T10:12:02.998989+05:30"
  }
}
```

**400 Bad Request (Wrong User Type):**
```json
{
  "detail": "This endpoint is for general users only. Use /auth/operator-profile for operator users."
}
```

**500 Internal Server Error:**
```json
{
  "status": "error",
  "code": 500,
  "message": "Failed to get profile",
  "meta": {
    "requestId": "uuid-string",
    "timestamp": "2024-01-16T10:12:02.998989+05:30"
  }
}
```

## Best Practices

1. **Use the unified endpoint** (`/auth/profile`) unless you specifically need type validation
2. **Check the `user_type` field** in responses to handle different user types appropriately
3. **Use type-specific endpoints** when you need to ensure only certain user types can access data
4. **Handle errors gracefully** and provide appropriate fallbacks
5. **Test with both user types** to ensure your application works correctly

## Security Considerations

- All endpoints require valid JWT authentication
- User type detection is automatic and secure
- Type-specific endpoints provide additional validation
- Profile updates are scoped to the authenticated user only
- Sensitive fields like `role` and `operator_id` cannot be modified through profile updates

## Support

For questions or issues with the unified profile endpoints, please contact:
- Email: support@blubus.com
- Documentation: https://docs.blubus.com/profile
- API Reference: `/docs` (Swagger UI)
