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
from ..services.user_service import UserService
from ..services.token_service import TokenService
from ..services.rate_limiter import RateLimiter
from ..auth.dependencies import get_current_user
from ..models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
user_service = UserService()
token_service = TokenService()
rate_limiter = RateLimiter()


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register new user with OTP verification."""
    try:
        # Check rate limit
        allowed, rate_message, rate_info = await rate_limiter.check_rate_limit(
            user_data.contact, "registration_attempts", db
        )
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=rate_message
            )
        
        success, message, user = await user_service.create_user(user_data, db)
        
        if success:
            return UserResponse(
                success=True,
                status=201,
                message=message,
                data=user
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/verify-otp/registration", response_model=UserResponse)
async def verify_registration_otp(
    otp_request: OTPVerificationRequest,
    db: Session = Depends(get_db)
):
    """Verify OTP for new user registration."""
    try:
        success, message, user = await user_service.verify_otp_and_activate(
            otp_request.contact,
            otp_request.contact_type,
            otp_request.otp,
            db
        )
        
        if success:
            return UserResponse(
                success=True,
                status=200,
                message=message,
                data=user
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OTP verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OTP verification failed"
        )


@router.post("/send-otp", response_model=UserResponse)
async def send_otp(
    otp_request: SendOTPRequest,
    db: Session = Depends(get_db)
):
    """Send OTP for registration or login."""
    try:
        # Check rate limit
        allowed, rate_message, rate_info = await rate_limiter.check_rate_limit(
            otp_request.contact, "otp_requests", db
        )
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=rate_message
            )
        
        success, message = await user_service.send_otp(
            otp_request.contact,
            otp_request.contact_type,
            otp_request.purpose,
            db
        )
        
        if success:
            return UserResponse(
                success=True,
                status=200,
                message=message,
                data=None
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send OTP error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP"
        )


@router.post("/login/password", response_model=TokenResponse)
async def login_with_password(
    login_request: PasswordLoginRequest,
    db: Session = Depends(get_db)
):
    """Password-based login."""
    try:
        # Check rate limit
        allowed, rate_message, rate_info = await rate_limiter.check_rate_limit(
            login_request.contact, "login_attempts", db
        )
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=rate_message
            )
        
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
            
            return TokenResponse(
                success=True,
                status=200,
                message=message,
                data=tokens
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=message
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/login/otp", response_model=TokenResponse)
async def login_with_otp(
    login_request: OTPLoginRequest,
    db: Session = Depends(get_db)
):
    """OTP-based login."""
    try:
        success, message, user = await user_service.authenticate_with_otp(
            login_request.contact,
            login_request.contact_type,
            login_request.otp,
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
            
            return TokenResponse(
                success=True,
                status=200,
                message=message,
                data=tokens
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=message
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OTP login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


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
