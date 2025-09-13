"""
Database models for BluBus Pulse backend application.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Table, Text, JSON, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import uuid
import enum


# Enums
class ContactType(str, enum.Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"


class MembershipStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"


# Association table for many-to-many relationship between routes and bus stops
route_stops = Table(
    'route_stops',
    Base.metadata,
    Column('route_id', Integer, ForeignKey('routes.id'), primary_key=True),
    Column('bus_stop_id', Integer, ForeignKey('bus_stops.id'), primary_key=True),
    Column('stop_order', Integer, nullable=False)  # Order of stops in the route
)


class BusStop(Base):
    """Model for bus stops."""
    __tablename__ = "bus_stops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    address = Column(String(500), nullable=True)
    is_active = Column(Integer, default=1)  # 1 for active, 0 for inactive
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    routes = relationship("Route", secondary=route_stops, back_populates="stops")

    def __repr__(self):
        return f"<BusStop(id={self.id}, name='{self.name}')>"


class Route(Base):
    """Model for bus routes."""
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    estimated_duration = Column(Integer, nullable=True)  # in minutes
    is_active = Column(Integer, default=1)  # 1 for active, 0 for inactive
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    stops = relationship("BusStop", secondary=route_stops, back_populates="routes")
    buses = relationship("Bus", back_populates="route")

    def __repr__(self):
        return f"<Route(id={self.id}, name='{self.name}')>"


class Bus(Base):
    """Model for buses."""
    __tablename__ = "buses"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey('routes.id'), nullable=False)
    bus_number = Column(String(50), nullable=False, index=True)
    current_stop_id = Column(Integer, ForeignKey('bus_stops.id'), nullable=True)
    next_stop_id = Column(Integer, ForeignKey('bus_stops.id'), nullable=True)
    estimated_arrival = Column(Integer, nullable=True)  # in minutes
    status = Column(String(50), default="in_transit")  # in_transit, at_stop, out_of_service
    capacity = Column(Integer, default=50)
    current_passengers = Column(Integer, default=0)
    is_active = Column(Integer, default=1)  # 1 for active, 0 for inactive
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    route = relationship("Route", back_populates="buses")
    current_stop = relationship("BusStop", foreign_keys=[current_stop_id])
    next_stop = relationship("BusStop", foreign_keys=[next_stop_id])

    def __repr__(self):
        return f"<Bus(id={self.id}, bus_number='{self.bus_number}', route_id={self.route_id})>"


class BusLocation(Base):
    """Model for tracking bus locations over time."""
    __tablename__ = "bus_locations"

    id = Column(Integer, primary_key=True, index=True)
    bus_id = Column(Integer, ForeignKey('buses.id'), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed = Column(Float, nullable=True)  # in km/h
    direction = Column(Float, nullable=True)  # in degrees
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    bus = relationship("Bus")

    def __repr__(self):
        return f"<BusLocation(bus_id={self.bus_id}, lat={self.latitude}, lng={self.longitude})>"


# Operator Management Models
class Operator(Base):
    """Model for bus operators/companies."""
    __tablename__ = "operators"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    contact_email = Column(String(255), nullable=False, unique=True, index=True)
    contact_phone = Column(String(20), nullable=True)
    business_license = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    status = Column(String(50), default="PENDING", index=True)  # PENDING, ACTIVE, SUSPENDED, REJECTED
    verification_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    documents = relationship("OperatorDocument", back_populates="operator", cascade="all, delete-orphan")
    users = relationship("OperatorUser", back_populates="operator", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Operator(id={self.id}, company_name='{self.company_name}', status='{self.status}')>"


class OperatorDocument(Base):
    """Model for operator documents stored in S3."""
    __tablename__ = "operator_documents"

    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(Integer, ForeignKey('operators.id'), nullable=False, index=True)
    doc_type = Column(String(50), nullable=False, index=True)  # RC, PERMIT, INSURANCE, etc.
    file_key = Column(String(500), nullable=False, unique=True)  # S3 object key
    file_url = Column(String(1000), nullable=True)  # S3 URL
    file_name = Column(String(255), nullable=True)  # Original filename
    file_size = Column(Integer, nullable=True)  # File size in bytes
    content_type = Column(String(100), nullable=True)  # MIME type
    status = Column(String(50), default="UPLOADED", index=True)  # UPLOADED, VERIFIED, REJECTED
    uploaded_by = Column(String(255), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    verified_at = Column(DateTime(timezone=True), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    verification_notes = Column(Text, nullable=True)
    document_metadata = Column(JSON, nullable=True)  # OCR text, verification results, etc.

    # Relationships
    operator = relationship("Operator", back_populates="documents")

    def __repr__(self):
        return f"<OperatorDocument(id={self.id}, operator_id={self.operator_id}, doc_type='{self.doc_type}', status='{self.status}')>"


class OperatorUser(Base):
    """Model for operator admin users."""
    __tablename__ = "operator_users"

    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(Integer, ForeignKey('operators.id'), nullable=False, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    role = Column(String(50), default="ADMIN", index=True)  # ADMIN, MANAGER, VIEWER
    is_active = Column(Boolean, default=True, index=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    operator = relationship("Operator", back_populates="users")

    def __repr__(self):
        return f"<OperatorUser(id={self.id}, email='{self.email}', operator_id={self.operator_id}, role='{self.role}')>"


class EmailTemplate(Base):
    """Model for SES email templates."""
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    subject = Column(String(255), nullable=False)
    html_template = Column(Text, nullable=False)
    text_template = Column(Text, nullable=True)
    variables = Column(JSON, nullable=True)  # Template variables schema
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<EmailTemplate(id={self.id}, name='{self.name}')>"


class EmailLog(Base):
    """Model for tracking sent emails."""
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(Integer, ForeignKey('operators.id'), nullable=True, index=True)
    template_name = Column(String(100), nullable=True)
    recipient_email = Column(String(255), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    status = Column(String(50), default="SENT", index=True)  # SENT, DELIVERED, BOUNCED, COMPLAINED
    ses_message_id = Column(String(255), nullable=True, unique=True)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    bounced_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<EmailLog(id={self.id}, recipient='{self.recipient_email}', status='{self.status}')>"


# New Authentication System Models
class User(Base):
    """Model for system users with multi-channel authentication."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    mobile = Column(String(20), unique=True, nullable=True, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=True)  # Nullable for OTP-only users
    source = Column(SQLEnum(ContactType), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    is_email_verified = Column(Boolean, default=False)
    is_mobile_verified = Column(Boolean, default=False)
    login_attempts = Column(Integer, default=0)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organizations = relationship("Organization", back_populates="owner")
    memberships = relationship("OrganizationMembership", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', mobile='{self.mobile}')>"


class Organization(Base):
    """Model for organizations/companies."""
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    settings = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="organizations")
    memberships = relationship("OrganizationMembership", back_populates="organization")

    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}')>"


class OrganizationMembership(Base):
    """Model for user-organization relationships with roles and departments."""
    __tablename__ = "organization_memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False, index=True)
    roles = Column(ARRAY(String), default=[], nullable=False)
    departments = Column(ARRAY(String), default=[], nullable=False)
    status = Column(SQLEnum(MembershipStatus), default=MembershipStatus.ACTIVE, index=True)
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="memberships")
    organization = relationship("Organization", back_populates="memberships")

    def __repr__(self):
        return f"<OrganizationMembership(user_id={self.user_id}, organization_id={self.organization_id}, roles={self.roles})>"


class OTPRecord(Base):
    """Model for storing OTP codes temporarily."""
    __tablename__ = "otp_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    contact = Column(String(255), nullable=False, index=True)
    contact_type = Column(SQLEnum(ContactType), nullable=False)
    otp_code = Column(String(10), nullable=False)
    purpose = Column(String(50), nullable=False)  # registration, login, password_reset, etc.
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_used = Column(Boolean, default=False, index=True)
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<OTPRecord(contact='{self.contact}', purpose='{self.purpose}', expires_at={self.expires_at})>"


class TokenBlacklist(Base):
    """Model for blacklisted JWT tokens."""
    __tablename__ = "token_blacklist"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    token_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    token_type = Column(String(20), nullable=False)  # access, refresh
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    blacklisted_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<TokenBlacklist(token_id='{self.token_id}', user_id={self.user_id})>"
