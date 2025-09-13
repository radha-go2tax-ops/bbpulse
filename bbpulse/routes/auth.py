"""
Authentication API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..database import get_db
from ..models import OperatorUser
from ..schemas import (
    UserLogin, Token, UserResponse, PasswordResetRequest, PasswordReset
)
from ..auth.dependencies import get_current_user
from ..auth.jwt_handler import JWTHandler
from ..services.email_service import SESEmailService
from ..tasks.email_tasks import send_password_reset_email
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
jwt_handler = JWTHandler()
email_service = SESEmailService()


@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """Authenticate user and return tokens."""
    try:
        # Find user by email
        user = db.query(OperatorUser).filter(
            OperatorUser.email == user_credentials.email
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Verify password
        if not jwt_handler.verify_password(user_credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Create tokens
        tokens = jwt_handler.create_token_pair(user.id, user.operator_id)
        
        logger.info(f"User {user.id} logged in successfully")
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    try:
        # Verify refresh token
        payload = jwt_handler.verify_token(refresh_token, "refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user from database
        user = db.query(OperatorUser).filter(OperatorUser.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new token pair
        tokens = jwt_handler.create_token_pair(user.id, user.operator_id)
        
        logger.info(f"Tokens refreshed for user {user.id}")
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: OperatorUser = Depends(get_current_user)
):
    """Get current user information."""
    return current_user


@router.post("/forgot-password")
async def forgot_password(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Send password reset email."""
    try:
        # Find user by email
        user = db.query(OperatorUser).filter(
            OperatorUser.email == request.email
        ).first()
        
        if not user:
            # Don't reveal if user exists or not
            return {"message": "If the email exists, a password reset link has been sent"}
        
        # Generate reset token (in real implementation, use proper token generation)
        reset_token = jwt_handler.create_access_token(
            user.id, 
            user.operator_id,
            expires_delta=timedelta(hours=24)
        )
        
        # Send password reset email
        send_password_reset_email.delay(user.email, reset_token)
        
        logger.info(f"Password reset email sent to {request.email}")
        return {"message": "If the email exists, a password reset link has been sent"}
        
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset email"
        )


@router.post("/reset-password")
async def reset_password(
    request: PasswordReset,
    db: Session = Depends(get_db)
):
    """Reset user password using token."""
    try:
        # Verify reset token
        payload = jwt_handler.verify_token(request.token, "access")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )
        
        # Get user from database
        user = db.query(OperatorUser).filter(OperatorUser.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Hash new password
        new_password_hash = jwt_handler.get_password_hash(request.new_password)
        
        # Update password
        user.password_hash = new_password_hash
        db.commit()
        
        logger.info(f"Password reset for user {user.id}")
        return {"message": "Password reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


@router.post("/logout")
async def logout(
    current_user: OperatorUser = Depends(get_current_user)
):
    """Logout user (client should discard tokens)."""
    # In a stateless JWT system, logout is handled client-side
    # You could implement token blacklisting here if needed
    logger.info(f"User {current_user.id} logged out")
    return {"message": "Logged out successfully"}


@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: OperatorUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password."""
    try:
        # Verify current password
        if not jwt_handler.verify_password(current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_password_hash = jwt_handler.get_password_hash(new_password)
        
        # Update password
        current_user.password_hash = new_password_hash
        db.commit()
        
        logger.info(f"Password changed for user {current_user.id}")
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )

