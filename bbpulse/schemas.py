"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
import re

# Standardized Response Schemas
class MetaInfo(BaseModel):
    """Metadata for API responses."""
    requestId: str = Field(..., example="f29dbe3c-1234-4567-8901-abcdef123456")
    timestamp: str = Field(..., example="2024-01-01T10:00:00Z")
    pagination: Optional[Dict[str, Any]] = Field(None, example={
        "page": 1,
        "pageSize": 20,
        "total": 42
    })

    def model_dump(self, **kwargs):
        """Override to exclude None values."""
        data = super().model_dump(**kwargs)
        return {k: v for k, v in data.items() if v is not None}


class ErrorDetail(BaseModel):
    """Individual error detail."""
    field: str = Field(..., example="email")
    issue: str = Field(..., example="Invalid email format")


class BaseResponse(BaseModel):
    """Base response schema for all API endpoints."""
    status: str
    code: int
    data: Optional[Any] = None
    meta: Dict[str, Any]

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SuccessResponse(BaseResponse):
    """Standardized success response."""
    status: str = "success"


class ErrorResponse(BaseModel):
    """Standardized error response."""
    status: str = "error"
    code: int
    message: str
    errors: Optional[List[ErrorDetail]] = None
    meta: Dict[str, Any]

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "status": "error",
                "code": 400,
                "message": "Validation failed",
                "errors": [
                    {
                        "field": "email",
                        "issue": "Invalid email format"
                    },
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
        }


# Base schemas
class BusStopBase(BaseModel):
    name: str = Field(..., max_length=255)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    description: Optional[str] = None
    address: Optional[str] = Field(None, max_length=500)


class BusStopCreate(BusStopBase):
    pass


class BusStopUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    description: Optional[str] = None
    address: Optional[str] = Field(None, max_length=500)
    is_active: Optional[int] = Field(None, ge=0, le=1)


class BusStop(BusStopBase):
    id: int
    is_active: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RouteBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    estimated_duration: Optional[int] = Field(None, ge=0)


class RouteCreate(RouteBase):
    stop_ids: List[int] = Field(default_factory=list)


class RouteUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    estimated_duration: Optional[int] = Field(None, ge=0)
    is_active: Optional[int] = Field(None, ge=0, le=1)


class Route(RouteBase):
    id: int
    is_active: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    stops: List[BusStop] = []

    class Config:
        from_attributes = True


class BusBase(BaseModel):
    bus_number: str = Field(..., max_length=50)
    route_id: int
    current_stop_id: Optional[int] = None
    next_stop_id: Optional[int] = None
    estimated_arrival: Optional[int] = Field(None, ge=0)
    status: str = Field(default="in_transit", max_length=50)
    capacity: int = Field(default=50, ge=1)
    current_passengers: int = Field(default=0, ge=0)


class BusCreate(BusBase):
    pass


class BusUpdate(BaseModel):
    bus_number: Optional[str] = Field(None, max_length=50)
    route_id: Optional[int] = None
    current_stop_id: Optional[int] = None
    next_stop_id: Optional[int] = None
    estimated_arrival: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, max_length=50)
    capacity: Optional[int] = Field(None, ge=1)
    current_passengers: Optional[int] = Field(None, ge=0)
    is_active: Optional[int] = Field(None, ge=0, le=1)


class Bus(BusBase):
    id: int
    is_active: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    route: Optional[Route] = None
    current_stop: Optional[BusStop] = None
    next_stop: Optional[BusStop] = None

    class Config:
        from_attributes = True


class BusLocationBase(BaseModel):
    bus_id: int
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    speed: Optional[float] = Field(None, ge=0)
    direction: Optional[float] = Field(None, ge=0, le=360)


class BusLocationCreate(BusLocationBase):
    pass


class BusLocation(BusLocationBase):
    id: int
    recorded_at: datetime

    class Config:
        from_attributes = True


class BusTracking(BaseModel):
    bus_id: int
    bus_number: str
    current_stop: Optional[BusStop] = None
    next_stop: Optional[BusStop] = None
    estimated_arrival: Optional[int] = None
    status: str
    last_location: Optional[BusLocation] = None

    class Config:
        from_attributes = True


# Operator Management Schemas
class OperatorBase(BaseModel):
    company_name: str = Field(..., max_length=255)
    contact_email: EmailStr
    contact_phone: Optional[str] = Field(None, max_length=20)
    business_license: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)


class OperatorCreate(OperatorBase):
    pass


class OperatorUpdate(BaseModel):
    company_name: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=20)
    business_license: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    status: Optional[str] = Field(None, max_length=50)
    verification_notes: Optional[str] = None


class Operator(OperatorBase):
    id: int
    status: str
    verification_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OperatorResponse(Operator):
    documents: List["OperatorDocument"] = Field(default_factory=list)
    users: List["User"] = Field(default_factory=list)


# Standardized List Response Schemas
class OperatorsListResponse(BaseResponse):
    """Standardized response for operators list endpoints."""
    status: str = "success"
    data: List[OperatorResponse] = Field(default_factory=list)

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "code": 200,
                "data": [
                    {
                        "id": 12,
                        "company_name": "Mumbai Bus Services",
                        "contact_email": "operator@example.com",
                        "contact_phone": "+919731990033",
                        "business_license": "BL123456789",
                        "address": "123 Main Street, Andheri",
                        "city": "Mumbai",
                        "state": "Maharashtra",
                        "country": "India",
                        "postal_code": "400001",
                        "status": "PENDING",
                        "verification_notes": None,
                        "created_at": "2024-01-16T10:12:02.998989+05:30",
                        "updated_at": None,
                        "verified_at": None,
                        "documents": [],
                        "users": [
                            {
                                "id": 8,
                                "email": "operator@example.com",
                                "first_name": "Operator",
                                "last_name": "Admin",
                                "role": "ADMIN",
                                "operator_id": 12,
                                "is_active": True
                            }
                        ]
                    }
                ],
                "meta": {
                    "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
                    "timestamp": "2024-01-16T10:12:02.998989+05:30",
                    "pagination": {
                        "page": 1,
                        "pageSize": 100,
                        "total": 1
                    }
                }
            }
        }


class OperatorDetailResponse(BaseResponse):
    """Standardized response for single operator detail endpoints."""
    status: str = "success"
    data: Optional[OperatorResponse] = None

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "code": 200,
                "data": {
                    "id": 12,
                    "company_name": "Mumbai Bus Services",
                    "contact_email": "operator@example.com",
                    "contact_phone": "+919731990033",
                    "business_license": "BL123456789",
                    "address": "123 Main Street, Andheri",
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "country": "India",
                    "postal_code": "400001",
                    "status": "PENDING",
                    "verification_notes": None,
                    "created_at": "2024-01-16T10:12:02.998989+05:30",
                    "updated_at": None,
                    "verified_at": None,
                    "documents": [],
                    "users": [
                        {
                            "id": 8,
                            "email": "operator@example.com",
                            "first_name": "Operator",
                            "last_name": "Admin",
                            "role": "ADMIN",
                            "operator_id": 12,
                            "is_active": True
                        }
                    ]
                },
                "meta": {
                    "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
                    "timestamp": "2024-01-16T10:12:02.998989+05:30"
                }
            }
        }


class UsersListResponse(BaseResponse):
    """Standardized response for users list endpoints."""
    status: str = "success"
    data: List["User"] = Field(default_factory=list)

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "code": 200,
                "data": [
                    {
                        "id": 8,
                        "email": "operator@example.com",
                        "first_name": "Operator",
                        "last_name": "Admin",
                        "role": "ADMIN",
                        "operator_id": 12,
                        "is_active": True
                    },
                    {
                        "id": 9,
                        "email": "manager@example.com",
                        "first_name": "Manager",
                        "last_name": "User",
                        "role": "MANAGER",
                        "operator_id": 12,
                        "is_active": True
                    }
                ],
                "meta": {
                    "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
                    "timestamp": "2024-01-16T10:12:02.998989+05:30",
                    "pagination": {
                        "page": 1,
                        "pageSize": 50,
                        "total": 2
                    }
                }
            }
        }


class DocumentsListResponse(BaseResponse):
    """Standardized response for documents list endpoints."""
    status: str = "success"
    data: List["OperatorDocument"] = Field(default_factory=list)

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "code": 200,
                "data": [
                    {
                        "id": 1,
                        "operator_id": 12,
                        "doc_type": "BUSINESS_LICENSE",
                        "file_name": "business_license.pdf",
                        "file_size": 1024000,
                        "content_type": "application/pdf",
                        "file_key": "documents/12/business_license_20240116.pdf",
                        "status": "VERIFIED",
                        "uploaded_at": "2024-01-16T10:00:00Z",
                        "verified_at": "2024-01-16T10:30:00Z",
                        "expiry_date": "2025-01-16T10:00:00Z",
                        "uploaded_by": "admin@example.com"
                    }
                ],
                "meta": {
                    "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
                    "timestamp": "2024-01-16T10:12:02.998989+05:30",
                    "pagination": {
                        "page": 1,
                        "pageSize": 50,
                        "total": 1
                    }
                }
            }
        }


class RequiredDocumentsListResponse(BaseResponse):
    """Standardized response for required documents list endpoints."""
    status: str = "success"
    data: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "code": 200,
                "data": [
                    {
                        "type": "RC",
                        "name": "Registration Certificate",
                        "required": True,
                        "status": "VERIFIED",
                        "uploaded": True
                    },
                    {
                        "type": "PERMIT",
                        "name": "Operating Permit",
                        "required": True,
                        "status": "PENDING",
                        "uploaded": True
                    },
                    {
                        "type": "INSURANCE",
                        "name": "Insurance Certificate",
                        "required": True,
                        "status": "NOT_UPLOADED",
                        "uploaded": False
                    },
                    {
                        "type": "TAX_CERTIFICATE",
                        "name": "Tax Clearance Certificate",
                        "required": True,
                        "status": "NOT_UPLOADED",
                        "uploaded": False
                    },
                    {
                        "type": "PAN_CARD",
                        "name": "PAN Card",
                        "required": False,
                        "status": "VERIFIED",
                        "uploaded": True
                    },
                    {
                        "type": "GST_CERTIFICATE",
                        "name": "GST Certificate",
                        "required": False,
                        "status": "NOT_UPLOADED",
                        "uploaded": False
                    }
                ],
                "meta": {
                    "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
                    "timestamp": "2024-01-16T10:12:02.998989+05:30"
                }
            }
        }


# Document Management Schemas
class DocumentUploadRequest(BaseModel):
    filename: str = Field(..., max_length=255)
    content_type: str = Field(..., max_length=100)
    doc_type: str = Field(..., max_length=50)
    expiry_days: Optional[int] = Field(365, ge=1, le=3650)


class PresignResponse(BaseModel):
    upload_url: str
    file_key: str
    fields: Dict[str, Any]
    expires_in: int


class DocumentRegisterRequest(BaseModel):
    file_key: str = Field(..., max_length=500)
    doc_type: str = Field(..., max_length=50)
    expiry_date: Optional[datetime] = None
    uploaded_by: Optional[str] = Field(None, max_length=255)


class OperatorDocumentBase(BaseModel):
    doc_type: str = Field(..., max_length=50)
    file_name: Optional[str] = Field(None, max_length=255)
    file_size: Optional[int] = Field(None, ge=0)
    content_type: Optional[str] = Field(None, max_length=100)
    expiry_date: Optional[datetime] = None


class OperatorDocumentCreate(OperatorDocumentBase):
    file_key: str = Field(..., max_length=500)
    uploaded_by: Optional[str] = Field(None, max_length=255)


class OperatorDocumentUpdate(BaseModel):
    status: Optional[str] = Field(None, max_length=50)
    verification_notes: Optional[str] = None
    document_metadata: Optional[Dict[str, Any]] = None


class OperatorDocument(OperatorDocumentBase):
    id: int
    operator_id: int
    file_key: str
    file_url: Optional[str] = None
    status: str
    uploaded_by: Optional[str] = None
    uploaded_at: datetime
    verified_at: Optional[datetime] = None
    verification_notes: Optional[str] = None
    document_metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# User Management Schemas
class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    role: str = Field("ADMIN", max_length=50)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    operator_id: int


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(UserBase):
    id: int
    operator_id: int
    is_active: bool
    last_login: Optional[datetime] = None
    email_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserResponse(User):
    operator: Optional[Operator] = None


# Authentication Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    operator_id: Optional[int] = None


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


# Email Schemas
class EmailTemplateBase(BaseModel):
    name: str = Field(..., max_length=100)
    subject: str = Field(..., max_length=255)
    html_template: str
    text_template: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None


class EmailTemplateCreate(EmailTemplateBase):
    pass


class EmailTemplateUpdate(BaseModel):
    subject: Optional[str] = Field(None, max_length=255)
    html_template: Optional[str] = None
    text_template: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class EmailTemplate(EmailTemplateBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EmailSendRequest(BaseModel):
    template_name: str = Field(..., max_length=100)
    recipient_email: EmailStr
    template_data: Dict[str, Any] = Field(default_factory=dict)
    operator_id: Optional[int] = None


# Health Check Schemas
class HealthCheck(BaseModel):
    status: str
    service: str
    timestamp: datetime
    version: str = "1.0.0"


class AWSHealthCheck(HealthCheck):
    s3_status: str
    ses_status: str
    redis_status: str


# Note: Forward references will be resolved automatically by Pydantic


# New Authentication System Schemas
class ContactType(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"




# User Registration Schemas
class UserCreate(BaseModel):
    contact: str = Field(..., min_length=3, max_length=255, example="user@example.com")
    contact_type: ContactType = Field(..., example=ContactType.EMAIL)
    password: str = Field(..., min_length=8, max_length=100, example="SecurePass123!")
    full_name: str = Field(..., min_length=2, max_length=255, example="John Doe")

    class Config:
        schema_extra = {
            "example": {
                "contact": "user@example.com",
                "contact_type": "email",
                "password": "SecurePass123!",
                "full_name": "John Doe"
            }
        }

    @validator('contact')
    def validate_contact(cls, v, values):
        contact_type = values.get('contact_type')
        if contact_type == ContactType.EMAIL:
            # Basic email validation
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
                raise ValueError('Invalid email format')
        elif contact_type == ContactType.WHATSAPP:
            # Basic phone number validation (international format)
            if not re.match(r'^\+?[1-9]\d{1,14}$', v):
                raise ValueError('Invalid phone number format')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    mobile: Optional[str] = Field(None, min_length=10, max_length=20)

    @validator('mobile')
    def validate_mobile(cls, v):
        if v and not re.match(r'^\+?[1-9]\d{1,14}$', v):
            raise ValueError('Invalid phone number format')
        return v


class UserInDB(BaseModel):
    id: str
    email: Optional[str] = None
    mobile: Optional[str] = None
    full_name: str
    source: ContactType
    is_active: bool
    is_email_verified: bool
    is_mobile_verified: bool
    login_attempts: int
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserResponse(BaseResponse):
    """Response schema for user operations."""
    status: str = "success"
    data: Optional[UserInDB] = None

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "code": 201,
                "data": {
                    "id": "uuid-string",
                    "email": "user@example.com",
                    "mobile": None,
                    "full_name": "John Doe",
                    "source": "email",
                    "is_active": True,
                    "is_email_verified": False,
                    "is_mobile_verified": False,
                    "login_attempts": 0,
                    "last_login": None,
                    "created_at": "2024-01-01T10:00:00Z",
                    "updated_at": "2024-01-01T10:00:00Z"
                },
                "meta": {
                    "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
                    "timestamp": "2024-01-01T10:00:00Z"
                }
            }
        }


# OTP Schemas
class OTPRequest(BaseModel):
    contact: str = Field(..., min_length=3, max_length=255, example="user@example.com")
    contact_type: ContactType = Field(..., example=ContactType.EMAIL)
    purpose: str = Field(..., min_length=3, max_length=50, example="registration")  # registration, login, password_reset

    class Config:
        schema_extra = {
            "example": {
                "contact": "user@example.com",
                "contact_type": "email",
                "purpose": "registration"
            }
        }

    @validator('contact')
    def validate_contact(cls, v, values):
        contact_type = values.get('contact_type')
        if contact_type == ContactType.EMAIL:
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
                raise ValueError('Invalid email format')
        elif contact_type == ContactType.WHATSAPP:
            if not re.match(r'^\+?[1-9]\d{1,14}$', v):
                raise ValueError('Invalid phone number format')
        return v


class OTPVerificationRequest(BaseModel):
    contact: str = Field(..., min_length=3, max_length=255, example="user@example.com")
    contact_type: ContactType = Field(..., example=ContactType.EMAIL)
    otp: str = Field(..., min_length=4, max_length=10, example="123456")
    purpose: str = Field(..., min_length=3, max_length=50, example="registration")

    class Config:
        schema_extra = {
            "example": {
                "contact": "user@example.com",
                "contact_type": "email",
                "otp": "123456",
                "purpose": "registration"
            }
        }


class SendOTPRequest(BaseModel):
    contact: str = Field(..., min_length=3, max_length=255, example="user@example.com")
    contact_type: ContactType = Field(..., example=ContactType.EMAIL)
    purpose: str = Field(default="registration", min_length=3, max_length=50, example="registration")

    class Config:
        schema_extra = {
            "example": {
                "contact": "user@example.com",
                "contact_type": "email",
                "purpose": "registration"
            }
        }


# Login Schemas
class PasswordLoginRequest(BaseModel):
    contact: str = Field(..., min_length=3, max_length=255, example="user@example.com")
    contact_type: ContactType = Field(..., example=ContactType.EMAIL)
    password: str = Field(..., min_length=8, max_length=100, example="SecurePass123!")

    class Config:
        schema_extra = {
            "example": {
                "contact": "user@example.com",
                "contact_type": "email",
                "password": "SecurePass123!"
            }
        }


class OTPLoginRequest(BaseModel):
    contact: str = Field(..., min_length=3, max_length=255, example="user@example.com")
    contact_type: ContactType = Field(..., example=ContactType.EMAIL)
    otp: str = Field(..., min_length=4, max_length=10, example="123456")

    class Config:
        schema_extra = {
            "example": {
                "contact": "user@example.com",
                "contact_type": "email",
                "otp": "123456"
            }
        }


# Token Schemas
class TokenData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenResponse(BaseResponse):
    """Response schema for token operations."""
    status: str = "success"
    data: TokenData

    class Config:
        schema_extra = {
            "example": {
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
        }


class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10)




# Profile Schemas
class UserProfileResponse(BaseResponse):
    """Response schema for user profile operations."""
    status: str = "success"
    data: Optional[Dict[str, Any]] = None


class UpdateProfile(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    mobile: Optional[str] = Field(None, min_length=10, max_length=20)

    @validator('mobile')
    def validate_mobile(cls, v):
        if v and not re.match(r'^\+?[1-9]\d{1,14}$', v):
            raise ValueError('Invalid phone number format')
        return v


# Logout Schema
class LogoutResponse(BaseResponse):
    """Response schema for logout operations."""
    status: str = "success"
    data: Optional[Dict[str, Any]] = None


# Operator User Creation Schema
class OperatorUserCreate(BaseModel):
    """Schema for creating operator users."""
    email: EmailStr = Field(..., example="admin@company.com")
    mobile: Optional[str] = Field(None, min_length=10, max_length=20, example="+919876543210")
    password: str = Field(..., min_length=8, max_length=100, example="SecurePass123!")
    first_name: str = Field(..., min_length=2, max_length=100, example="John")
    last_name: str = Field(..., min_length=2, max_length=100, example="Doe")
    role: str = Field(default="ADMIN", example="ADMIN")

    class Config:
        schema_extra = {
            "example": {
                "email": "admin@company.com",
                "mobile": "+919876543210",
                "password": "SecurePass123!",
                "first_name": "John",
                "last_name": "Doe",
                "role": "ADMIN"
            }
        }

    @validator('mobile')
    def validate_mobile(cls, v):
        if v and not re.match(r'^\+?[1-9]\d{1,14}$', v):
            raise ValueError('Invalid phone number format')
        return v


# Operator Registration Schemas
class OperatorRegistrationData(BaseModel):
    """Schema for operator registration data."""
    company_name: str = Field(..., min_length=2, max_length=255, example="Mumbai Bus Services")
    contact_phone: str = Field(..., min_length=10, max_length=20, example="+919876543210")
    business_license: Optional[str] = Field(None, max_length=100, example="BL123456789")
    address: Optional[str] = Field(None, example="123 Main Street, Andheri")
    city: Optional[str] = Field(None, max_length=100, example="Mumbai")
    state: Optional[str] = Field(None, max_length=100, example="Maharashtra")
    country: Optional[str] = Field(None, max_length=100, example="India")
    postal_code: Optional[str] = Field(None, max_length=20, example="400001")

    class Config:
        schema_extra = {
            "example": {
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
    
    @validator('contact_phone')
    def validate_phone(cls, v):
        if not re.match(r'^\+?[1-9]\d{1,14}$', v):
            raise ValueError('Invalid phone number format')
        return v


class OperatorRegistrationRequest(BaseModel):
    """Request schema for operator registration with OTP verification."""
    contact: str = Field(..., min_length=10, max_length=20, example="+919876543210")
    contact_type: ContactType = Field(default=ContactType.WHATSAPP, example=ContactType.WHATSAPP)
    otp: str = Field(..., min_length=4, max_length=10, example="123456")
    registration_data: OperatorRegistrationData

    class Config:
        schema_extra = {
            "example": {
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
        }
    
    @validator('contact')
    def validate_contact(cls, v, values):
        contact_type = values.get('contact_type')
        if contact_type == ContactType.WHATSAPP:
            if not re.match(r'^\+?[1-9]\d{1,14}$', v):
                raise ValueError('Invalid phone number format')
        elif contact_type == ContactType.EMAIL:
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
                raise ValueError('Invalid email format')
        return v


class OperatorRegistrationResponse(BaseResponse):
    """Response schema for operator registration."""
    status: str = "success"
    data: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
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
                        "temporary_password": "TempPass1123!",
                        "message": "Please change your password after first login"
                    }
                },
                "meta": {
                    "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
                    "timestamp": "2024-01-01T10:00:00Z"
                }
            }
        }


class OperatorOTPResponse(BaseResponse):
    """Response schema for OTP operations."""
    status: str = "success"
    data: Optional[Dict[str, Any]] = None


# Import Enum for proper type hints

