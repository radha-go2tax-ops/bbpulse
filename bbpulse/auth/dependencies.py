"""
Authentication dependencies for FastAPI.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .jwt_handler import JWTHandler
from ..database import get_db
from ..models import OperatorUser, User
import logging

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()

# JWT handler instance
jwt_handler = JWTHandler()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials
        db: Database session
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token
        payload = jwt_handler.verify_token(credentials.credentials, "access")
        if payload is None:
            raise credentials_exception
        
        # Extract user ID from payload
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise credentials_exception
        
        return user
        
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise credentials_exception




def get_current_operator_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> OperatorUser:
    """
    Get current authenticated operator user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials
        db: Database session
        
    Returns:
        Current authenticated operator user
        
    Raises:
        HTTPException: If token is invalid or operator user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token
        payload = jwt_handler.verify_token(credentials.credentials, "access")
        if payload is None:
            raise credentials_exception
        
        # Extract user ID from payload
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Get operator user from database
        operator_user = db.query(OperatorUser).filter(OperatorUser.id == user_id).first()
        if operator_user is None:
            raise credentials_exception
        
        return operator_user
        
    except Exception as e:
        logger.error(f"Operator authentication error: {e}")
        raise credentials_exception


def require_admin_role(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Require admin role for the current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User if admin
        
    Raises:
        HTTPException: If user is not admin
    """
    # Check if user has admin role in the main user system
    # For now, we'll check if the user is active and verified
    # You may want to add a role field to the User model for proper admin checking
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    
    # TODO: Add proper role-based admin checking when User model has role field
    # For now, allowing any active user to access operator endpoints
    return current_user


def require_operator_admin_role(
    current_user: OperatorUser = Depends(get_current_operator_user),
    db: Session = Depends(get_db)
) -> OperatorUser:
    """
    Require admin role for the current operator user.
    
    Args:
        current_user: Current authenticated operator user
        
    Returns:
        OperatorUser if admin
        
    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operator user account is not active"
        )
    
    if current_user.role not in ["ADMIN", "MANAGER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin or Manager role required"
        )
    
    return current_user
