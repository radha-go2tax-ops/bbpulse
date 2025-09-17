"""
Unified Profile API routes for both User and OperatorUser profile management.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import UnifiedProfileResponse, UpdateProfile
from ..utils.response_utils import create_success_response, raise_http_exception
from ..auth.dependencies import get_current_user_unified
from ..models import User, OperatorUser
from typing import Union
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["unified-profile"])


@router.get("/profile", response_model=UnifiedProfileResponse)
async def get_unified_profile(
    current_user: Union[User, OperatorUser] = Depends(get_current_user_unified)
):
    """
    Get current user profile - automatically detects user type and returns appropriate data.
    
    This unified endpoint works for both:
    - General users (passengers/end-users) who registered through the public system
    - Operator users (company employees) who manage bus operations
    
    **When to use:**
    - Use this endpoint when you need to get profile information but don't know the user type
    - Use specific endpoints (/auth/user-profile or /auth/operator-profile) when you know the user type
    
    **Response includes:**
    - user_type: "user" or "operator_user" to identify the user type
    - data: Profile information appropriate for the user type
    """
    try:
        # Determine user type and format data accordingly
        if isinstance(current_user, OperatorUser):
            profile_data = {
                "id": current_user.id,
                "email": current_user.email,
                "mobile": current_user.mobile,
                "first_name": current_user.first_name,
                "last_name": current_user.last_name,
                "role": current_user.role,
                "operator_id": current_user.operator_id,
                "is_active": current_user.is_active,
                "email_verified": current_user.email_verified,
                "mobile_verified": current_user.mobile_verified,
                "last_login": current_user.last_login,
                "created_at": current_user.created_at,
                "updated_at": current_user.updated_at
            }
            user_type = "operator_user"
        else:  # isinstance(current_user, User)
            profile_data = {
                "id": str(current_user.id),
                "email": current_user.email,
                "mobile": current_user.mobile,
                "full_name": current_user.full_name,
                "source": current_user.source,
                "is_active": current_user.is_active,
                "is_email_verified": current_user.is_email_verified,
                "is_mobile_verified": current_user.is_mobile_verified,
                "login_attempts": current_user.login_attempts,
                "last_login": current_user.last_login,
                "created_at": current_user.created_at,
                "updated_at": current_user.updated_at
            }
            user_type = "user"
        
        return UnifiedProfileResponse(
            success=True,
            status=200,
            message="Profile retrieved successfully",
            data=profile_data,
            user_type=user_type
        )
        
    except Exception as e:
        logger.error(f"Get unified profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get profile"
        )


@router.get("/user-profile", response_model=UnifiedProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user_unified)
):
    """
    Get profile for general users (passengers/end-users).
    
    **When to use:**
    - When you specifically need profile data for general system users
    - For passengers who registered through the public registration system
    - When you know the user is not an operator employee
    
    **Response includes:**
    - user_type: "user"
    - data: General user profile information (email, mobile, full_name, source, etc.)
    """
    if not isinstance(current_user, User):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint is for general users only. Use /auth/operator-profile for operator users."
        )
    
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
            "login_attempts": current_user.login_attempts,
            "last_login": current_user.last_login,
            "created_at": current_user.created_at,
            "updated_at": current_user.updated_at
        }
        
        return UnifiedProfileResponse(
            success=True,
            status=200,
            message="User profile retrieved successfully",
            data=profile_data,
            user_type="user"
        )
        
    except Exception as e:
        logger.error(f"Get user profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )


@router.get("/operator-profile", response_model=UnifiedProfileResponse)
async def get_operator_profile(
    current_user: OperatorUser = Depends(get_current_user_unified)
):
    """
    Get profile for operator users (company employees).
    
    **When to use:**
    - When you specifically need profile data for operator users
    - For company employees who manage bus operations
    - When you know the user is an operator employee
    
    **Response includes:**
    - user_type: "operator_user"
    - data: Operator user profile information (email, mobile, first_name, last_name, role, operator_id, etc.)
    """
    if not isinstance(current_user, OperatorUser):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint is for operator users only. Use /auth/user-profile for general users."
        )
    
    try:
        profile_data = {
            "id": current_user.id,
            "email": current_user.email,
            "mobile": current_user.mobile,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "role": current_user.role,
            "operator_id": current_user.operator_id,
            "is_active": current_user.is_active,
            "email_verified": current_user.email_verified,
            "mobile_verified": current_user.mobile_verified,
            "last_login": current_user.last_login,
            "created_at": current_user.created_at,
            "updated_at": current_user.updated_at
        }
        
        return UnifiedProfileResponse(
            success=True,
            status=200,
            message="Operator profile retrieved successfully",
            data=profile_data,
            user_type="operator_user"
        )
        
    except Exception as e:
        logger.error(f"Get operator profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get operator profile"
        )


@router.put("/profile", response_model=UnifiedProfileResponse)
async def update_unified_profile(
    update_data: UpdateProfile,
    current_user: Union[User, OperatorUser] = Depends(get_current_user_unified),
    db: Session = Depends(get_db)
):
    """
    Update current user profile - automatically detects user type and updates appropriate fields.
    
    **When to use:**
    - When you need to update profile information but don't know the user type
    - Use specific endpoints (/auth/user-profile or /auth/operator-profile) when you know the user type
    
    **Supported updates:**
    - General users: full_name, email, mobile
    - Operator users: full_name, email, mobile (role and operator_id cannot be changed)
    """
    try:
        if isinstance(current_user, OperatorUser):
            # Update operator user
            if update_data.full_name:
                current_user.first_name = update_data.full_name.split(' ')[0] if ' ' in update_data.full_name else update_data.full_name
                current_user.last_name = update_data.full_name.split(' ', 1)[1] if ' ' in update_data.full_name else ""
            
            if update_data.email:
                current_user.email = update_data.email
            
            if update_data.mobile:
                current_user.mobile = update_data.mobile
            
            current_user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(current_user)
            
            profile_data = {
                "id": current_user.id,
                "email": current_user.email,
                "mobile": current_user.mobile,
                "first_name": current_user.first_name,
                "last_name": current_user.last_name,
                "role": current_user.role,
                "operator_id": current_user.operator_id,
                "is_active": current_user.is_active,
                "email_verified": current_user.email_verified,
                "mobile_verified": current_user.mobile_verified,
                "last_login": current_user.last_login,
                "created_at": current_user.created_at,
                "updated_at": current_user.updated_at
            }
            user_type = "operator_user"
            
        else:  # isinstance(current_user, User)
            # Update general user
            if update_data.full_name:
                current_user.full_name = update_data.full_name
            
            if update_data.email:
                current_user.email = update_data.email
            
            if update_data.mobile:
                current_user.mobile = update_data.mobile
            
            current_user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(current_user)
            
            profile_data = {
                "id": str(current_user.id),
                "email": current_user.email,
                "mobile": current_user.mobile,
                "full_name": current_user.full_name,
                "source": current_user.source,
                "is_active": current_user.is_active,
                "is_email_verified": current_user.is_email_verified,
                "is_mobile_verified": current_user.is_mobile_verified,
                "login_attempts": current_user.login_attempts,
                "last_login": current_user.last_login,
                "created_at": current_user.created_at,
                "updated_at": current_user.updated_at
            }
            user_type = "user"
        
        return UnifiedProfileResponse(
            success=True,
            status=200,
            message="Profile updated successfully",
            data=profile_data,
            user_type=user_type
        )
        
    except Exception as e:
        logger.error(f"Update unified profile error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
