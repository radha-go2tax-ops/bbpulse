"""
Operator management API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Operator, OperatorUser
from ..schemas import (
    OperatorCreate, OperatorUpdate, OperatorResponse, 
    UserCreate, UserResponse, UserUpdate
)
from ..auth.dependencies import get_current_user, require_admin_role
from ..services.email_service import SESEmailService
from ..tasks.operator_tasks import send_operator_notification
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/operators", tags=["operators"])
email_service = SESEmailService()


@router.post("/", response_model=OperatorResponse, status_code=status.HTTP_201_CREATED)
async def create_operator(
    operator_data: OperatorCreate,
    db: Session = Depends(get_db)
):
    """Create a new operator account."""
    try:
        # Check if operator with same email already exists
        existing_operator = db.query(Operator).filter(
            Operator.contact_email == operator_data.contact_email
        ).first()
        
        if existing_operator:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Operator with this email already exists"
            )
        
        # Create operator
        operator = Operator(**operator_data.dict())
        db.add(operator)
        db.commit()
        db.refresh(operator)
        
        # Send account creation notification
        send_operator_notification.delay(
            operator_id=operator.id,
            notification_type="account_created"
        )
        
        logger.info(f"Created operator {operator.id}: {operator.company_name}")
        return operator
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating operator: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create operator"
        )


@router.get("/{operator_id}", response_model=OperatorResponse)
async def get_operator(
    operator_id: int,
    db: Session = Depends(get_db),
    current_user: OperatorUser = Depends(get_current_user)
):
    """Get operator details."""
    # Check if user has access to this operator
    if current_user.operator_id != operator_id and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operator not found"
        )
    
    return operator


@router.put("/{operator_id}", response_model=OperatorResponse)
async def update_operator(
    operator_id: int,
    operator_data: OperatorUpdate,
    db: Session = Depends(get_db),
    current_user: OperatorUser = Depends(get_current_user)
):
    """Update operator information."""
    # Check if user has access to this operator
    if current_user.operator_id != operator_id and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operator not found"
        )
    
    # Update operator fields
    update_data = operator_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(operator, field, value)
    
    db.commit()
    db.refresh(operator)
    
    logger.info(f"Updated operator {operator_id}")
    return operator


@router.get("/", response_model=List[OperatorResponse])
async def list_operators(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: OperatorUser = Depends(require_admin_role)
):
    """List all operators (admin only)."""
    query = db.query(Operator)
    
    if status:
        query = query.filter(Operator.status == status)
    
    operators = query.offset(skip).limit(limit).all()
    return operators


@router.post("/{operator_id}/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_operator_user(
    operator_id: int,
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: OperatorUser = Depends(require_admin_role)
):
    """Create a new user for an operator (admin only)."""
    # Check if operator exists
    operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operator not found"
        )
    
    # Check if user with same email already exists
    existing_user = db.query(OperatorUser).filter(
        OperatorUser.email == user_data.email
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Hash password
    from ..auth.jwt_handler import JWTHandler
    jwt_handler = JWTHandler()
    hashed_password = jwt_handler.get_password_hash(user_data.password)
    
    # Create user
    user = OperatorUser(
        operator_id=operator_id,
        email=user_data.email,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Send welcome email
    from ..tasks.email_tasks import send_welcome_email
    send_welcome_email.delay(user.id)
    
    logger.info(f"Created user {user.id} for operator {operator_id}")
    return user


@router.get("/{operator_id}/users", response_model=List[UserResponse])
async def list_operator_users(
    operator_id: int,
    db: Session = Depends(get_db),
    current_user: OperatorUser = Depends(get_current_user)
):
    """List users for an operator."""
    # Check if user has access to this operator
    if current_user.operator_id != operator_id and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    users = db.query(OperatorUser).filter(
        OperatorUser.operator_id == operator_id
    ).all()
    
    return users


@router.put("/{operator_id}/users/{user_id}", response_model=UserResponse)
async def update_operator_user(
    operator_id: int,
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: OperatorUser = Depends(get_current_user)
):
    """Update operator user."""
    # Check if user has access to this operator
    if current_user.operator_id != operator_id and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    user = db.query(OperatorUser).filter(
        OperatorUser.id == user_id,
        OperatorUser.operator_id == operator_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update user fields
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"Updated user {user_id} for operator {operator_id}")
    return user


@router.delete("/{operator_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_operator_user(
    operator_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: OperatorUser = Depends(require_admin_role)
):
    """Delete operator user (admin only)."""
    user = db.query(OperatorUser).filter(
        OperatorUser.id == user_id,
        OperatorUser.operator_id == operator_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()
    
    logger.info(f"Deleted user {user_id} for operator {operator_id}")


@router.post("/{operator_id}/suspend", response_model=OperatorResponse)
async def suspend_operator(
    operator_id: int,
    reason: str,
    db: Session = Depends(get_db),
    current_user: OperatorUser = Depends(require_admin_role)
):
    """Suspend an operator (admin only)."""
    operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operator not found"
        )
    
    operator.status = "SUSPENDED"
    operator.verification_notes = reason
    db.commit()
    db.refresh(operator)
    
    # Send suspension notification
    send_operator_notification.delay(
        operator_id=operator_id,
        notification_type="account_suspended",
        data={"reason": reason}
    )
    
    logger.info(f"Suspended operator {operator_id}: {reason}")
    return operator


@router.post("/{operator_id}/activate", response_model=OperatorResponse)
async def activate_operator(
    operator_id: int,
    db: Session = Depends(get_db),
    current_user: OperatorUser = Depends(require_admin_role)
):
    """Activate an operator (admin only)."""
    operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operator not found"
        )
    
    operator.status = "ACTIVE"
    db.commit()
    db.refresh(operator)
    
    # Send activation notification
    from ..tasks.email_tasks import send_operator_activation_email
    send_operator_activation_email.delay(operator_id)
    
    logger.info(f"Activated operator {operator_id}")
    return operator
