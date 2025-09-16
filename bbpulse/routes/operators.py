"""
Operator management API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Operator, OperatorUser, User
from ..schemas import (
    OperatorCreate, OperatorUpdate, OperatorResponse, 
    UserCreate, UserResponse, UserUpdate,
    OperatorRegistrationRequest, OperatorRegistrationResponse,
    OperatorUserCreate
)
from ..utils.response_utils import (
    create_success_response, raise_http_exception, raise_validation_error,
    raise_authentication_error, raise_authorization_error, raise_not_found_error,
    raise_rate_limit_error, raise_server_error
)
from ..auth.dependencies import get_current_operator_user, require_operator_admin_role
from ..services.email_service import SESEmailService
from ..services.otp_service import OTPService
from ..services.rate_limiter import RateLimiter
from ..tasks.operator_tasks import send_operator_notification
from ..models import ContactType
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/operators", tags=["operators"])
email_service = SESEmailService()
otp_service = OTPService()
rate_limiter = RateLimiter()


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
    current_user: OperatorUser = Depends(get_current_operator_user)
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
    current_user: OperatorUser = Depends(get_current_operator_user)
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
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: OperatorUser = Depends(get_current_operator_user)
):
    """List all operators (operator users only)."""
    query = db.query(Operator)
    
    if status:
        query = query.filter(Operator.status == status)
    
    if search:
        query = query.filter(
            Operator.company_name.ilike(f"%{search}%") |
            Operator.contact_phone.ilike(f"%{search}%") |
            Operator.contact_email.ilike(f"%{search}%")
        )
    
    operators = query.offset(skip).limit(limit).all()
    return operators


@router.get("/public", response_model=List[OperatorResponse])
async def list_operators_public(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = "ACTIVE",
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List active operators (public endpoint).
    
    This endpoint returns a list of active operators that can be viewed by anyone.
    It supports pagination, filtering by status, and searching by company name, city, or state.
    
    **Query Parameters:**
    - `skip` (integer, optional): Number of records to skip (default: 0)
    - `limit` (integer, optional): Maximum number of records to return (default: 50, max: 100)
    - `status` (string, optional): Filter by operator status (default: "ACTIVE")
    - `search` (string, optional): Search by company name, city, or state
    
    **Response:**
    - Array of operator objects with basic information
    - Each operator includes: id, company_name, contact_phone, status, city, state, created_at
    
    **Example Request:**
    ```
    GET /operators/public?search=Mumbai&status=ACTIVE&skip=0&limit=20
    ```
    
    **Example Success Response:**
    ```json
    [
        {
            "id": 1,
            "company_name": "Mumbai Bus Services",
            "contact_phone": "+919876543210",
            "status": "ACTIVE",
            "city": "Mumbai",
            "state": "Maharashtra",
            "created_at": "2024-01-01T10:00:00Z"
        },
        {
            "id": 2,
            "company_name": "Delhi Transport Co",
            "contact_phone": "+919876543211",
            "status": "ACTIVE",
            "city": "Delhi",
            "state": "Delhi",
            "created_at": "2024-01-01T11:00:00Z"
        }
    ]
    ```
    
    **Example Request with Search:**
    ```
    GET /operators/public?search=Mumbai&limit=10
    ```
    
    **Example Request with Pagination:**
    ```
    GET /operators/public?skip=20&limit=10
    ```
    """
    query = db.query(Operator)
    
    # Only show active operators for public access
    if status:
        query = query.filter(Operator.status == status)
    else:
        query = query.filter(Operator.status == "ACTIVE")
    
    if search:
        query = query.filter(
            Operator.company_name.ilike(f"%{search}%") |
            Operator.city.ilike(f"%{search}%") |
            Operator.state.ilike(f"%{search}%")
        )
    
    operators = query.offset(skip).limit(limit).all()
    return operators


@router.post("/{operator_id}/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_operator_user(
    operator_id: int,
    user_data: OperatorUserCreate,
    db: Session = Depends(get_db),
    current_user: OperatorUser = Depends(require_operator_admin_role)
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
    
    # Check if user with same mobile already exists (if mobile provided)
    if user_data.mobile:
        existing_mobile_user = db.query(OperatorUser).filter(
            OperatorUser.mobile == user_data.mobile
        ).first()
        
        if existing_mobile_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this mobile number already exists"
            )
    
    # Hash password
    from ..auth.jwt_handler import JWTHandler
    jwt_handler = JWTHandler()
    hashed_password = jwt_handler.get_password_hash(user_data.password)
    
    # Create user
    user = OperatorUser(
        operator_id=operator_id,
        email=user_data.email,
        mobile=user_data.mobile,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role,
        email_verified=False,
        mobile_verified=False
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
    current_user: OperatorUser = Depends(get_current_operator_user)
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
    current_user: OperatorUser = Depends(get_current_operator_user)
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
    current_user: OperatorUser = Depends(require_operator_admin_role)
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
    current_user: OperatorUser = Depends(require_operator_admin_role)
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
    current_user: OperatorUser = Depends(require_operator_admin_role)
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


# Operator Registration Endpoint
@router.post(
    "/register", 
    response_model=OperatorRegistrationResponse,
    responses={
        201: {
            "description": "Operator registered successfully",
            "content": {
                "application/json": {
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
            }
        },
        400: {
            "description": "Validation error or invalid OTP",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "code": 400,
                        "message": "Invalid or expired OTP",
                        "meta": {
                            "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
                            "timestamp": "2024-01-01T10:00:00Z"
                        }
                    }
                }
            }
        },
        409: {
            "description": "Operator already exists",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "code": 409,
                        "message": "Operator with this contact already exists",
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
async def register_operator(
    registration_request: OperatorRegistrationRequest,
    db: Session = Depends(get_db)
):
    """
    Register operator after OTP verification.
    
    This endpoint registers a new bus operator after verifying the OTP sent to their contact.
    The operator account is created with PENDING status and requires admin approval.
    
    **Request Body:**
    - `contact` (string): Phone number or email address
    - `contact_type` (enum): "whatsapp" or "email"
    - `otp` (string): 6-digit OTP code received
    - `registration_data` (object): Operator company information
      - `company_name` (string): Name of the bus company
      - `contact_phone` (string): Primary contact phone number
      - `business_license` (string): Business license number
      - `address` (string): Company address
      - `city` (string): City name
      - `state` (string): State name
      - `country` (string): Country name
      - `postal_code` (string): Postal/ZIP code
    
    **Response:**
    - `status` (string): "success"
    - `code` (integer): HTTP status code
    - `data` (object): Operator information
    - `meta` (object): Request metadata with requestId and timestamp
    
    **Example Request:**
    ```json
    {
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
    ```
    
    **Example Success Response:**
    ```json
    {
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
    
    **Example Error Response (Duplicate Operator):**
    ```json
    {
        "status": "error",
        "code": 400,
        "message": "Operator with this contact already exists",
        "meta": {
            "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
            "timestamp": "2024-01-01T10:00:00Z"
        }
    }
    ```
    """
    try:
        # First, validate the registration data before consuming OTP
        # This ensures OTP is only consumed if all data is valid
        operator_data = registration_request.registration_data
        
        # Check if operator with this contact already exists
        if registration_request.contact_type == ContactType.WHATSAPP:
            existing_operator = db.query(Operator).filter(
                Operator.contact_phone == registration_request.contact
            ).first()
        else:  # EMAIL
            existing_operator = db.query(Operator).filter(
                Operator.contact_email == registration_request.contact
            ).first()
        
        if existing_operator:
            raise_validation_error("Operator with this contact already exists")
        
        # Verify OTP only after data validation passes
        otp_valid = await otp_service.verify_otp(
            contact=registration_request.contact,
            contact_type=registration_request.contact_type,
            otp=registration_request.otp,
            purpose="registration",
            db=db
        )
        
        if not otp_valid:
            raise_validation_error("Invalid or expired OTP")
        
        # Set contact information based on contact type
        if registration_request.contact_type == ContactType.WHATSAPP:
            contact_email = f"operator_{registration_request.contact}@temp.com"  # Temporary email
            contact_phone = registration_request.contact
        else:  # EMAIL
            contact_email = registration_request.contact
            contact_phone = operator_data.contact_phone  # Use phone from registration data
        
        operator = Operator(
            company_name=operator_data.company_name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            business_license=operator_data.business_license,
            address=operator_data.address,
            city=operator_data.city,
            state=operator_data.state,
            country=operator_data.country,
            postal_code=operator_data.postal_code,
            status="PENDING"
        )
        
        db.add(operator)
        db.commit()
        db.refresh(operator)
        
        # Create default operator user for login access
        from ..auth.jwt_handler import JWTHandler
        jwt_handler = JWTHandler()
        
        # Generate a temporary password (operator will need to change this)
        temp_password = f"TempPass{operator.id}123!"
        hashed_password = jwt_handler.get_password_hash(temp_password)
        
        # Create operator user
        operator_user = OperatorUser(
            operator_id=operator.id,
            email=contact_email,
            mobile=contact_phone,
            password_hash=hashed_password,
            first_name="Operator",
            last_name="Admin",
            role="ADMIN",
            is_active=True,
            email_verified=True,  # Since OTP was verified
            mobile_verified=True  # Since OTP was verified
        )
        
        db.add(operator_user)
        db.commit()
        db.refresh(operator_user)
        
        # Send account creation notification
        send_operator_notification.delay(
            operator_id=operator.id,
            notification_type="account_created"
        )
        
        logger.info(f"Created operator {operator.id}: {operator.company_name} with user {operator_user.id}")
        
        # Prepare response data with login information
        # Convert operator to dict to avoid serialization issues
        operator_dict = {
            "id": operator.id,
            "company_name": operator.company_name,
            "contact_email": operator.contact_email,
            "contact_phone": operator.contact_phone,
            "business_license": operator.business_license,
            "address": operator.address,
            "city": operator.city,
            "state": operator.state,
            "country": operator.country,
            "postal_code": operator.postal_code,
            "status": operator.status,
            "created_at": operator.created_at,
            "updated_at": operator.updated_at
        }
        
        response_data = {
            "operator": operator_dict,
            "login_credentials": {
                "email": contact_email,
                "mobile": contact_phone,
                "temporary_password": temp_password,
                "message": "Please change your password after first login. You can use email or mobile for OTP login."
            }
        }
        
        return create_success_response(
            data=response_data,
            code=201
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering operator: {e}")
        db.rollback()
        raise_server_error("Failed to register operator")

