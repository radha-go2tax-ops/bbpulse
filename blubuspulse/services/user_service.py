"""
User Service for handling user registration, authentication, and management.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..models import User, Organization, OrganizationMembership, ContactType, UserStatus
from ..schemas import UserCreate, UserInDB, OrganizationCreate
from ..auth.jwt_handler import JWTHandler
from .otp_service import OTPService
from ..settings import settings

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing user operations."""
    
    def __init__(self):
        self.jwt_handler = JWTHandler()
        self.otp_service = OTPService()
        self.max_login_attempts = getattr(settings, 'max_login_attempts', 5)
    
    async def create_user(self, user_data: UserCreate, db: Session) -> Tuple[bool, str, Optional[UserInDB]]:
        """
        Create a new user with OTP verification.
        
        Args:
            user_data: User creation data
            db: Database session
            
        Returns:
            Tuple of (success, message, user_data)
        """
        try:
            # Check if user already exists
            existing_user = await self._get_user_by_contact(
                user_data.contact, 
                user_data.contact_type, 
                db
            )
            
            if existing_user:
                return False, f"User with this {user_data.contact_type} already exists", None
            
            # Hash password
            hashed_password = self.jwt_handler.get_password_hash(user_data.password)
            
            # Create user record
            user = User(
                email=user_data.contact if user_data.contact_type == ContactType.EMAIL else None,
                mobile=user_data.contact if user_data.contact_type == ContactType.WHATSAPP else None,
                full_name=user_data.full_name,
                hashed_password=hashed_password,
                source=user_data.contact_type,
                is_active=True,
                is_email_verified=False,
                is_mobile_verified=False,
                login_attempts=0
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Create organization if provided
            organization = None
            if user_data.organization_name:
                organization = await self._create_organization(
                    user.id, 
                    user_data.organization_name, 
                    db
                )
            
            # Send OTP for verification
            otp_success, otp_message = await self.otp_service.send_otp(
                user_data.contact,
                user_data.contact_type,
                "registration",
                db
            )
            
            if not otp_success:
                logger.warning(f"Failed to send OTP to {user_data.contact}")
            
            # Convert to response format
            user_in_db = UserInDB(
                id=str(user.id),
                email=user.email,
                mobile=user.mobile,
                full_name=user.full_name,
                source=user.source,
                is_active=user.is_active,
                is_email_verified=user.is_email_verified,
                is_mobile_verified=user.is_mobile_verified,
                login_attempts=user.login_attempts,
                last_login=user.last_login,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            
            message = f"User created successfully. {otp_message}"
            return True, message, user_in_db
            
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Database integrity error creating user: {e}")
            return False, "User with this contact already exists", None
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating user: {e}")
            return False, "Failed to create user", None
    
    async def verify_otp_and_activate(
        self, 
        contact: str, 
        contact_type: ContactType, 
        otp: str, 
        db: Session
    ) -> Tuple[bool, str, Optional[UserInDB]]:
        """
        Verify OTP and activate user account.
        
        Args:
            contact: Email or phone number
            contact_type: Type of contact
            otp: OTP code
            db: Database session
            
        Returns:
            Tuple of (success, message, user_data)
        """
        try:
            # Verify OTP
            otp_valid = await self.otp_service.verify_otp(
                contact, 
                contact_type, 
                otp, 
                "registration",
                db
            )
            
            if not otp_valid:
                return False, "Invalid or expired OTP", None
            
            # Get user
            user = await self._get_user_by_contact(contact, contact_type, db)
            if not user:
                return False, "User not found", None
            
            # Activate user and mark contact as verified
            if contact_type == ContactType.EMAIL:
                user.is_email_verified = True
            else:
                user.is_mobile_verified = True
            
            user.is_active = True
            db.commit()
            
            # Convert to response format
            user_in_db = UserInDB(
                id=str(user.id),
                email=user.email,
                mobile=user.mobile,
                full_name=user.full_name,
                source=user.source,
                is_active=user.is_active,
                is_email_verified=user.is_email_verified,
                is_mobile_verified=user.is_mobile_verified,
                login_attempts=user.login_attempts,
                last_login=user.last_login,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            
            return True, "Account activated successfully", user_in_db
            
        except Exception as e:
            logger.error(f"Error verifying OTP: {e}")
            return False, "Failed to verify OTP", None
    
    async def authenticate_with_password(
        self, 
        contact: str, 
        contact_type: ContactType, 
        password: str, 
        db: Session
    ) -> Tuple[bool, str, Optional[UserInDB]]:
        """
        Authenticate user with password.
        
        Args:
            contact: Email or phone number
            contact_type: Type of contact
            password: User password
            db: Database session
            
        Returns:
            Tuple of (success, message, user_data)
        """
        try:
            # Get user
            user = await self._get_user_by_contact(contact, contact_type, db)
            if not user:
                return False, "Invalid credentials", None
            
            # Check if user is active
            if not user.is_active:
                return False, "Account is deactivated", None
            
            # Check login attempts
            if user.login_attempts >= self.max_login_attempts:
                return False, "Account locked due to too many failed attempts", None
            
            # Verify password
            if not self.jwt_handler.verify_password(password, user.hashed_password):
                # Increment login attempts
                user.login_attempts += 1
                db.commit()
                return False, "Invalid credentials", None
            
            # Reset login attempts and update last login
            user.login_attempts = 0
            user.last_login = datetime.utcnow()
            db.commit()
            
            # Convert to response format
            user_in_db = UserInDB(
                id=str(user.id),
                email=user.email,
                mobile=user.mobile,
                full_name=user.full_name,
                source=user.source,
                is_active=user.is_active,
                is_email_verified=user.is_email_verified,
                is_mobile_verified=user.is_mobile_verified,
                login_attempts=user.login_attempts,
                last_login=user.last_login,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            
            return True, "Authentication successful", user_in_db
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return False, "Authentication failed", None
    
    async def authenticate_with_otp(
        self, 
        contact: str, 
        contact_type: ContactType, 
        otp: str, 
        db: Session
    ) -> Tuple[bool, str, Optional[UserInDB]]:
        """
        Authenticate user with OTP.
        
        Args:
            contact: Email or phone number
            contact_type: Type of contact
            otp: OTP code
            db: Database session
            
        Returns:
            Tuple of (success, message, user_data)
        """
        try:
            # Verify OTP
            otp_valid = await self.otp_service.verify_otp(
                contact, 
                contact_type, 
                otp, 
                "login",
                db
            )
            
            if not otp_valid:
                return False, "Invalid or expired OTP", None
            
            # Get user
            user = await self._get_user_by_contact(contact, contact_type, db)
            if not user:
                return False, "User not found", None
            
            # Check if user is active
            if not user.is_active:
                return False, "Account is deactivated", None
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.commit()
            
            # Convert to response format
            user_in_db = UserInDB(
                id=str(user.id),
                email=user.email,
                mobile=user.mobile,
                full_name=user.full_name,
                source=user.source,
                is_active=user.is_active,
                is_email_verified=user.is_email_verified,
                is_mobile_verified=user.is_mobile_verified,
                login_attempts=user.login_attempts,
                last_login=user.last_login,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            
            return True, "Authentication successful", user_in_db
            
        except Exception as e:
            logger.error(f"Error authenticating user with OTP: {e}")
            return False, "Authentication failed", None
    
    async def send_otp(
        self, 
        contact: str, 
        contact_type: ContactType, 
        purpose: str = "login",
        db: Session = None
    ) -> Tuple[bool, str]:
        """
        Send OTP to user.
        
        Args:
            contact: Email or phone number
            contact_type: Type of contact
            purpose: Purpose of OTP
            db: Database session
            
        Returns:
            Tuple of (success, message)
        """
        try:
            return await self.otp_service.send_otp(contact, contact_type, purpose, db)
        except Exception as e:
            logger.error(f"Error sending OTP: {e}")
            return False, "Failed to send OTP"
    
    async def _get_user_by_contact(
        self, 
        contact: str, 
        contact_type: ContactType, 
        db: Session
    ) -> Optional[User]:
        """Get user by contact information."""
        if contact_type == ContactType.EMAIL:
            return db.query(User).filter(User.email == contact).first()
        else:
            return db.query(User).filter(User.mobile == contact).first()
    
    async def _create_organization(
        self, 
        user_id: str, 
        organization_name: str, 
        db: Session
    ) -> Optional[Organization]:
        """Create organization for user."""
        try:
            organization = Organization(
                name=organization_name,
                user_id=user_id,
                settings={}
            )
            
            db.add(organization)
            db.commit()
            db.refresh(organization)
            
            # Create membership for the user
            membership = OrganizationMembership(
                user_id=user_id,
                organization_id=organization.id,
                roles=["owner"],
                departments=["management"],
                status="active"
            )
            
            db.add(membership)
            db.commit()
            
            return organization
            
        except Exception as e:
            logger.error(f"Error creating organization: {e}")
            db.rollback()
            return None
