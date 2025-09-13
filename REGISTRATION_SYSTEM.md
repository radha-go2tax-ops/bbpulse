# Registration System Implementation

## Overview

This document describes the comprehensive registration system implemented for BluBus Plus, supporting multi-channel authentication (email and WhatsApp) with OTP verification, password-based login, and organization management.

## Features

### ✅ Multi-Channel Registration
- **Email Registration**: Users can register using email addresses
- **WhatsApp Registration**: Users can register using mobile numbers
- **OTP Verification**: Required for account activation
- **Password Security**: Strong password validation with bcrypt hashing

### ✅ Authentication Methods
- **Password-based Login**: Traditional username/password authentication
- **OTP-based Login**: Passwordless authentication via OTP
- **JWT Tokens**: Access and refresh token system
- **Token Blacklisting**: Secure logout with token revocation

### ✅ Security Features
- **Rate Limiting**: Protection against brute force attacks
- **Password Validation**: Strong password requirements
- **Account Lockout**: Protection after multiple failed attempts
- **OTP Expiration**: Time-limited OTP codes

### ✅ Organization Management
- **Automatic Organization Creation**: New users get their own organization
- **Role-based Access**: Support for different user roles
- **Department Management**: Users can be assigned to departments

## API Endpoints

### Registration Endpoints

#### POST `/auth/register`
Register a new user with OTP verification.

**Request Body:**
```json
{
  "contact": "user@example.com",
  "contact_type": "email",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "organization_name": "My Company"
}
```

**Response:**
```json
{
  "success": true,
  "status": 201,
  "message": "User created successfully. OTP sent to your email",
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "source": "email",
    "is_active": true,
    "is_email_verified": false,
    "is_mobile_verified": false,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### POST `/auth/verify-otp/registration`
Verify OTP for new user registration.

**Request Body:**
```json
{
  "contact": "user@example.com",
  "contact_type": "email",
  "otp": "123456",
  "purpose": "registration"
}
```

#### POST `/auth/send-otp`
Send OTP for registration or login.

**Request Body:**
```json
{
  "contact": "user@example.com",
  "contact_type": "email",
  "purpose": "registration"
}
```

### Login Endpoints

#### POST `/auth/login/password`
Password-based login.

**Request Body:**
```json
{
  "contact": "user@example.com",
  "contact_type": "email",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "success": true,
  "status": 200,
  "message": "Authentication successful",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

#### POST `/auth/login/otp`
OTP-based login.

**Request Body:**
```json
{
  "contact": "user@example.com",
  "contact_type": "email",
  "otp": "123456"
}
```

#### POST `/auth/refresh`
Refresh access token.

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Profile Management

#### GET `/auth/profile`
Get current user profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

#### PUT `/auth/profile`
Update user profile.

**Request Body:**
```json
{
  "full_name": "John Smith",
  "email": "john.smith@example.com",
  "mobile": "+1234567890"
}
```

#### POST `/auth/logout`
Logout and blacklist token.

**Headers:**
```
Authorization: Bearer <access_token>
```

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    mobile VARCHAR(20) UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255),
    source ENUM('email', 'whatsapp') NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_email_verified BOOLEAN DEFAULT FALSE,
    is_mobile_verified BOOLEAN DEFAULT FALSE,
    login_attempts INTEGER DEFAULT 0,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Organizations Table
```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    user_id UUID REFERENCES users(id),
    settings JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Organization Memberships Table
```sql
CREATE TABLE organization_memberships (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    roles TEXT[] DEFAULT '{}',
    departments TEXT[] DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'active',
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### OTP Records Table
```sql
CREATE TABLE otp_records (
    id UUID PRIMARY KEY,
    contact VARCHAR(255) NOT NULL,
    contact_type ENUM('email', 'whatsapp') NOT NULL,
    otp_code VARCHAR(10) NOT NULL,
    purpose VARCHAR(50) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Token Blacklist Table
```sql
CREATE TABLE token_blacklist (
    id UUID PRIMARY KEY,
    token_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id),
    token_type VARCHAR(20) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    blacklisted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/bbpulse

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# OTP
OTP_EXPIRE_MINUTES=5
MAX_LOGIN_ATTEMPTS=5

# WhatsApp
WA_API_URL=https://api.whatsapp.com
WA_API_TOKEN=your-whatsapp-token

# Redis
REDIS_URL=redis://localhost:6379/0

# AWS SES
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
SES_REGION=us-east-1
SES_SOURCE_EMAIL=noreply@blubus.com
```

## Security Features

### Password Requirements
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

### Rate Limiting
- **Login Attempts**: 5 attempts per 15 minutes
- **OTP Requests**: 3 requests per 5 minutes
- **Registration Attempts**: 3 attempts per 10 minutes
- **Password Reset**: 3 requests per 10 minutes

### Token Security
- JWT tokens with configurable expiration
- Refresh token rotation
- Token blacklisting on logout
- Secure token verification

## Usage Examples

### Complete Registration Flow

1. **Register User**
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "contact": "user@example.com",
    "contact_type": "email",
    "password": "SecurePass123!",
    "full_name": "John Doe",
    "organization_name": "My Company"
  }'
```

2. **Verify OTP**
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

3. **Login**
```bash
curl -X POST "http://localhost:8000/auth/login/password" \
  -H "Content-Type: application/json" \
  -d '{
    "contact": "user@example.com",
    "contact_type": "email",
    "password": "SecurePass123!"
  }'
```

### OTP Login Flow

1. **Request OTP**
```bash
curl -X POST "http://localhost:8000/auth/send-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "contact": "user@example.com",
    "contact_type": "email",
    "purpose": "login"
  }'
```

2. **Login with OTP**
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

#### Rate Limit Exceeded
```json
{
  "detail": "Too many OTP requests. Try again in 3 minutes"
}
```

#### Invalid Credentials
```json
{
  "detail": "Invalid credentials"
}
```

#### Account Locked
```json
{
  "detail": "Account locked due to too many failed attempts"
}
```

#### Invalid OTP
```json
{
  "detail": "Invalid or expired OTP"
}
```

## Testing

### Unit Tests
- User service methods
- OTP service functionality
- Token service operations
- Password validation

### Integration Tests
- Complete registration flow
- Login with both methods
- Token refresh mechanism
- Rate limiting

### End-to-End Tests
- Full user journey from registration to login
- Multi-channel authentication
- Error handling scenarios

## Monitoring

### Authentication Metrics
- Login success/failure rates
- OTP delivery success rates
- Token refresh patterns
- User registration trends

### Security Monitoring
- Failed login attempts
- Suspicious activity detection
- Token blacklist monitoring
- Rate limit violations

## Deployment

### Prerequisites
- PostgreSQL database
- Redis server
- AWS SES configured
- WhatsApp API access

### Steps
1. Install dependencies
2. Set up environment variables
3. Run database migrations
4. Start the application

### Production Considerations
- Use strong JWT secret keys
- Configure proper CORS settings
- Set up monitoring and logging
- Implement backup strategies
- Use HTTPS in production

## Future Enhancements

### Planned Features
- Social login integration
- Multi-factor authentication
- Biometric authentication
- Advanced role management
- Audit logging
- Account recovery flows

### Scalability Improvements
- Redis-based rate limiting
- Database connection pooling
- Caching strategies
- Load balancing
- Microservices architecture

