"""
Registration API routes for user registration and authentication.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import (
    UserCreate, UserResponse, OTPVerificationRequest, SendOTPRequest,
    PasswordLoginRequest, OTPLoginRequest, TokenResponse, TokenRefreshRequest,
    UserProfileResponse, UpdateProfile, LogoutResponse
)
from ..utils.response_utils import (
    create_success_response, raise_http_exception, raise_validation_error,
    raise_authentication_error, raise_rate_limit_error, raise_server_error
)
from ..services.user_service import UserService
from ..services.token_service import TokenService
from ..services.rate_limiter import RateLimiter
from ..auth.dependencies import get_current_user
from ..models import User, OperatorUser, ContactType
from ..services.otp_service import OTPService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
user_service = UserService()
token_service = TokenService()
otp_service = OTPService()
rate_limiter = RateLimiter()


@router.post(
    "/register", 
    response_model=UserResponse,
    responses={
        201: {
            "description": "User registered successfully",
            "content": {
                "application/json": {
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
            }
        },
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
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
                }
            }
        },
        429: {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "code": 429,
                        "message": "Too many registration attempts. Try again in 1 hour",
                        "meta": {
                            "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
                            "timestamp": "2024-01-01T10:00:00Z"
                        }
                    }
                }
            }
        }
    }
)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register new user with OTP verification.
    
    This endpoint creates a new user account and sends an OTP for verification.
    The user must verify the OTP before the account becomes active.
    
    **Request Body:**
    - `contact` (string): Email address or phone number
    - `contact_type` (enum): "email" or "whatsapp"
    - `password` (string): Strong password (min 8 chars, must contain uppercase, lowercase, digit, special char)
    - `full_name` (string): User's full name
    
    **Response:**
    - `status` (string): "success"
    - `code` (integer): HTTP status code
    - `data` (object): User information
    - `meta` (object): Request metadata with requestId and timestamp
    
    **Example Request:**
    ```json
    {
        "contact": "user@example.com",
        "contact_type": "email",
        "password": "SecurePass123!",
        "full_name": "John Doe"
    }
    ```
    
    **Example Success Response:**
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
    
    **Example Error Response:**
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
    """
    try:
        # Check rate limit
        allowed, rate_message, rate_info = await rate_limiter.check_rate_limit(
            user_data.contact, "registration_attempts", db
        )
        
        if not allowed:
            raise_rate_limit_error(rate_message)
        
        success, message, user = await user_service.create_user(user_data, db)
        
        if success:
            return create_success_response(
                data=user,
                code=201
            )
        else:
            raise_validation_error(message)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise_server_error("Registration failed")


@router.post("/verify-otp", response_model=UserResponse)
async def verify_otp(
    otp_request: OTPVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Verify OTP for registration or login based on purpose.
    
    This endpoint verifies the OTP code sent to the user's contact.
    For registration purpose, it activates the user account.
    For login purpose, it authenticates the user.
    
    **Request Body:**
    - `contact` (string): Email address or phone number
    - `contact_type` (enum): "email" or "whatsapp"
    - `otp` (string): 6-digit OTP code
    - `purpose` (string): Purpose of OTP - "registration" or "login"
    
    **Response:**
    - `status` (string): "success"
    - `code` (integer): HTTP status code
    - `data` (object): User information
    - `meta` (object): Request metadata with requestId and timestamp
    
    **Example Request:**
    ```json
    {
        "contact": "user@example.com",
        "contact_type": "email",
        "otp": "123456",
        "purpose": "registration"
    }
    ```
    
    **Example Success Response:**
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
    
    **Example Error Response (Invalid OTP):**
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
    """
    try:
        if otp_request.purpose == "registration":
            # For registration, activate the user
            success, message, user = await user_service.verify_otp_and_activate(
                otp_request.contact,
                otp_request.contact_type,
                otp_request.otp,
                db
            )
        elif otp_request.purpose == "login":
            # For login, just authenticate
            success, message, user = await user_service.authenticate_with_otp(
                otp_request.contact,
                otp_request.contact_type,
                otp_request.otp,
                db
            )
        else:
            raise_validation_error("Invalid purpose. Use 'registration' or 'login'")
        
        if success:
            return create_success_response(
                data=user,
                code=200
            )
        else:
            raise_validation_error(message)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OTP verification error: {e}")
        raise_server_error("OTP verification failed")


@router.post(
    "/send-otp", 
    response_model=UserResponse,
    responses={
        200: {
            "description": "OTP sent successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "code": 200,
                        "data": None,
                        "meta": {
                            "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
                            "timestamp": "2024-01-01T10:00:00Z"
                        }
                    }
                }
            }
        },
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "code": 400,
                        "message": "Invalid contact format",
                        "meta": {
                            "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
                            "timestamp": "2024-01-01T10:00:00Z"
                        }
                    }
                }
            }
        },
        429: {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "code": 429,
                        "message": "Too many OTP requests. Try again in 3 minutes",
                        "meta": {
                            "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
                            "timestamp": "2024-01-01T10:00:00Z"
                        }
                    }
                }
            }
        }
    }
)
async def send_otp(
    otp_request: SendOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Send OTP for registration or login.
    
    This endpoint sends a 6-digit OTP code to the specified contact (email or WhatsApp).
    The OTP expires in 5 minutes and can be used for a maximum of 3 attempts.
    
    **Request Body:**
    - `contact` (string): Email address or phone number
    - `contact_type` (enum): "email" or "whatsapp"
    - `purpose` (string): Purpose of OTP - "registration", "login", "password_reset"
    
    **Response:**
    - `status` (string): "success"
    - `code` (integer): HTTP status code
    - `data` (null): No data returned for OTP send
    - `meta` (object): Request metadata with requestId and timestamp
    
    **Example Request:**
    ```json
    {
        "contact": "user@example.com",
        "contact_type": "email",
        "purpose": "registration"
    }
    ```
    
    **Example Success Response:**
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
    
    **Example Error Response (Rate Limited):**
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
    """
    try:
        # Check rate limit
        allowed, rate_message, rate_info = await rate_limiter.check_rate_limit(
            otp_request.contact, "otp_requests", db
        )
        
        if not allowed:
            raise_rate_limit_error(rate_message)
        
        success, message = await user_service.send_otp(
            otp_request.contact,
            otp_request.contact_type,
            otp_request.purpose,
            db
        )
        
        if success:
            return create_success_response(
                data=None,
                code=200
            )
        else:
            raise_validation_error(message)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send OTP error: {e}")
        raise_server_error("Failed to send OTP")


@router.post("/login/password", response_model=TokenResponse)
async def login_with_password(
    login_request: PasswordLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Password-based login.
    
    This endpoint authenticates users using their contact (email/phone) and password.
    Returns JWT access and refresh tokens upon successful authentication.
    
    **Request Body:**
    - `contact` (string): Email address or phone number
    - `contact_type` (enum): "email" or "whatsapp"
    - `password` (string): User's password
    
    **Response:**
    - `status` (string): "success"
    - `code` (integer): HTTP status code
    - `data` (object): Token information
    - `meta` (object): Request metadata with requestId and timestamp
    
    **Example Request:**
    ```json
    {
        "contact": "user@example.com",
        "contact_type": "email",
        "password": "SecurePass123!"
    }
    ```
    
    **Example Success Response:**
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
    
    **Example Error Response (Invalid Credentials):**
    ```json
    {
        "status": "error",
        "code": 401,
        "message": "Authentication failed",
        "meta": {
            "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
            "timestamp": "2024-01-01T10:00:00Z"
        }
    }
    ```
    """
    try:
        # Check rate limit
        allowed, rate_message, rate_info = await rate_limiter.check_rate_limit(
            login_request.contact, "login_attempts", db
        )
        
        if not allowed:
            raise_rate_limit_error(rate_message)
        
        success, message, user = await user_service.authenticate_with_password(
            login_request.contact,
            login_request.contact_type,
            login_request.password,
            db
        )
        
        if success:
            # Create tokens
            tokens = await token_service.create_tokens(
                user_id=user.id,
                additional_claims={
                    "email": user.email,
                    "mobile": user.mobile,
                    "full_name": user.full_name
                }
            )
            
            return create_success_response(
                data=tokens,
                code=200
            )
        
        # If regular user authentication failed, try operator user
        from ..models import OperatorUser
        from ..auth.jwt_handler import JWTHandler
        from datetime import datetime
        jwt_handler = JWTHandler()
        
        # Look for operator user by email or mobile
        if login_request.contact_type == ContactType.EMAIL:
            operator_user = db.query(OperatorUser).filter(
                OperatorUser.email == login_request.contact
            ).first()
        else:  # WHATSAPP/MOBILE
            operator_user = db.query(OperatorUser).filter(
                OperatorUser.mobile == login_request.contact
            ).first()
        
        if not operator_user:
            raise_authentication_error("User not found. Please register first using /auth/register or /operators/register endpoint")
        
        if operator_user.is_active:
            # Verify password
            if jwt_handler.verify_password(login_request.password, operator_user.password_hash):
                # Update last login
                operator_user.last_login = datetime.utcnow()
                db.commit()
                
                # Create tokens for operator user
                tokens = jwt_handler.create_token_pair(str(operator_user.id), operator_user.operator_id)
                
                # Convert to expected format
                token_data = {
                    "access_token": tokens.access_token,
                    "refresh_token": tokens.refresh_token,
                    "token_type": "bearer",
                    "expires_in": 1800
                }
                
                return create_success_response(
                    data=token_data,
                    code=200
                )
            else:
                raise_authentication_error("Invalid credentials")
        else:
            raise_authentication_error("User not found. Please register first using /auth/register or /operators/register endpoint")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password login error: {e}")
        raise_server_error("Login failed")


@router.post("/login/otp", response_model=TokenResponse)
async def login_with_otp(
    login_request: OTPLoginRequest,
    db: Session = Depends(get_db)
):
    """
    OTP-based login for both regular users and operator users.
    
    This endpoint authenticates users using OTP verification.
    First send an OTP using /auth/send-otp with purpose "login",
    then use this endpoint to verify the OTP and get authentication tokens.
    
    **Supports:**
    - Regular users (User model) - email or mobile OTP
    - Operator users (OperatorUser model) - email or mobile OTP
    
    **Request Body:**
    - `contact` (string): Email address or phone number
    - `contact_type` (enum): "email" or "whatsapp"
    - `otp` (string): 6-digit OTP code received
    
    **Response:**
    - `status` (string): "success"
    - `code` (integer): HTTP status code
    - `data` (object): Token information
    - `meta` (object): Request metadata with requestId and timestamp
    
    **Example Request:**
    ```json
    {
        "contact": "user@example.com",
        "contact_type": "email",
        "otp": "123456"
    }
    ```
    
    **Example Success Response:**
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
    
    **Example Error Response (Invalid OTP):**
    ```json
    {
        "status": "error",
        "code": 401,
        "message": "Authentication failed",
        "meta": {
            "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
            "timestamp": "2024-01-01T10:00:00Z"
        }
    }
    ```
    """
    try:
        # Use the unified OTP verification with login purpose
        otp_request = OTPVerificationRequest(
            contact=login_request.contact,
            contact_type=login_request.contact_type,
            otp=login_request.otp,
            purpose="login"
        )
        
        # Try to authenticate as regular user first
        success, message, user = await user_service.authenticate_with_otp(
            otp_request.contact,
            otp_request.contact_type,
            otp_request.otp,
            db
        )
        
        if success:
            # Create tokens for regular user
            tokens = await token_service.create_tokens(
                user_id=user.id,
                additional_claims={
                    "email": user.email,
                    "mobile": user.mobile,
                    "full_name": user.full_name
                }
            )
            
            return create_success_response(
                data=tokens,
                code=200
            )
        
        # If regular user authentication failed, try operator user
        # OTP was already verified by authenticate_with_otp above
        
        # Look for operator user by email or mobile
        if otp_request.contact_type == ContactType.EMAIL:
            operator_user = db.query(OperatorUser).filter(
                OperatorUser.email == otp_request.contact
            ).first()
        else:  # WHATSAPP/MOBILE
            operator_user = db.query(OperatorUser).filter(
                OperatorUser.mobile == otp_request.contact
            ).first()
        
        if operator_user:
            logger.info(f"Found operator user: {operator_user.id}, active: {operator_user.is_active}")
            if operator_user.is_active:
                # Create tokens for operator user
                from ..auth.jwt_handler import JWTHandler
                jwt_handler = JWTHandler()
                tokens = jwt_handler.create_token_pair(str(operator_user.id), {"operator_id": operator_user.operator_id})
                logger.info(f"Tokens created successfully for operator user {operator_user.id}")
                
                # Add expires_in field to match schema
                tokens["expires_in"] = jwt_handler.access_token_expire_minutes * 60  # Convert to seconds
                
                return create_success_response(
                    data=tokens,
                    code=200
                )
            else:
                raise_authentication_error("Operator account is inactive")
        else:
            logger.warning(f"No operator user found for contact: {otp_request.contact}")
            # If neither user type found
            raise_authentication_error("User not found. Please register first using /auth/register or /operators/register endpoint")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OTP login error: {e}")
        raise_server_error("OTP login failed")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_request: TokenRefreshRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token."""
    try:
        tokens = await token_service.renew_tokens(refresh_request.refresh_token, db)
        
        if tokens:
            return TokenResponse(
                success=True,
                status=200,
                message="Tokens refreshed successfully",
                data=tokens
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout and blacklist token."""
    try:
        # In a real implementation, you would get the token from the request
        # and blacklist it. For now, we'll just return success.
        
        logger.info(f"User {current_user.id} logged out")
        return LogoutResponse(
            success=True,
            status=200,
            message="Logged out successfully"
        )
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/profile", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get authenticated user profile."""
    try:
        profile_data = {
            "id": str(current_user.id),
            "email": current_user.email,
            "mobile": current_user.mobile,
            "full_name": current_user.full_name,
            "source": current_user.source,
            "is_active": current_user.is_active,
            "is_email_verified": current_user.is_email_verified,
            "is_mobile_verified": current_user.is_mobile_verified,
            "last_login": current_user.last_login,
            "created_at": current_user.created_at
        }
        
        return UserProfileResponse(
            success=True,
            status=200,
            message="Profile retrieved successfully",
            data=profile_data
        )
        
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get profile"
        )


@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(
    update_data: UpdateProfile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile with OTP verification for contact changes."""
    try:
        # Update profile fields
        if update_data.full_name:
            current_user.full_name = update_data.full_name
        
        # For email/mobile changes, you would typically require OTP verification
        # This is a simplified version
        if update_data.email and update_data.email != current_user.email:
            current_user.email = update_data.email
            current_user.is_email_verified = False
        
        if update_data.mobile and update_data.mobile != current_user.mobile:
            current_user.mobile = update_data.mobile
            current_user.is_mobile_verified = False
        
        db.commit()
        
        profile_data = {
            "id": str(current_user.id),
            "email": current_user.email,
            "mobile": current_user.mobile,
            "full_name": current_user.full_name,
            "source": current_user.source,
            "is_active": current_user.is_active,
            "is_email_verified": current_user.is_email_verified,
            "is_mobile_verified": current_user.is_mobile_verified,
            "last_login": current_user.last_login,
            "created_at": current_user.created_at
        }
        
        return UserProfileResponse(
            success=True,
            status=200,
            message="Profile updated successfully",
            data=profile_data
        )
        
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )

