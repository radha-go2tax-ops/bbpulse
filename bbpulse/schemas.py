"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
import re


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


class MembershipStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"


# User Registration Schemas
class UserCreate(BaseModel):
    contact: str = Field(..., min_length=3, max_length=255)
    contact_type: ContactType
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=255)
    organization_name: Optional[str] = Field(None, min_length=2, max_length=255)

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


class UserResponse(BaseModel):
    success: bool
    status: int
    message: str
    data: Optional[UserInDB] = None


# OTP Schemas
class OTPRequest(BaseModel):
    contact: str = Field(..., min_length=3, max_length=255)
    contact_type: ContactType
    purpose: str = Field(..., min_length=3, max_length=50)  # registration, login, password_reset

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
    contact: str = Field(..., min_length=3, max_length=255)
    contact_type: ContactType
    otp: str = Field(..., min_length=4, max_length=10)
    purpose: str = Field(..., min_length=3, max_length=50)


class SendOTPRequest(BaseModel):
    contact: str = Field(..., min_length=3, max_length=255)
    contact_type: ContactType
    purpose: str = Field(default="registration", min_length=3, max_length=50)


# Login Schemas
class PasswordLoginRequest(BaseModel):
    contact: str = Field(..., min_length=3, max_length=255)
    contact_type: ContactType
    password: str = Field(..., min_length=8, max_length=100)


class OTPLoginRequest(BaseModel):
    contact: str = Field(..., min_length=3, max_length=255)
    contact_type: ContactType
    otp: str = Field(..., min_length=4, max_length=10)


# Token Schemas
class TokenData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenResponse(BaseModel):
    success: bool
    status: int
    message: str
    data: TokenData


class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10)


# Organization Schemas
class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    settings: Optional[Dict[str, Any]] = None


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    settings: Optional[Dict[str, Any]] = None


class OrganizationInDB(BaseModel):
    id: str
    name: str
    user_id: str
    settings: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrganizationResponse(BaseModel):
    success: bool
    status: int
    message: str
    data: Optional[OrganizationInDB] = None


# Membership Schemas
class MembershipCreate(BaseModel):
    user_id: str
    organization_id: str
    roles: List[str] = Field(default_factory=list)
    departments: List[str] = Field(default_factory=list)


class MembershipUpdate(BaseModel):
    roles: Optional[List[str]] = None
    departments: Optional[List[str]] = None
    status: Optional[MembershipStatus] = None


class MembershipInDB(BaseModel):
    id: str
    user_id: str
    organization_id: str
    roles: List[str]
    departments: List[str]
    status: MembershipStatus
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Profile Schemas
class UserProfileResponse(BaseModel):
    success: bool
    status: int
    message: str
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
class LogoutResponse(BaseModel):
    success: bool
    status: int
    message: str


# Import Enum for proper type hints

