"""
Utility functions for consistent API responses.
"""
import uuid
from datetime import datetime
from fastapi import HTTPException, status
from typing import Any, Optional, Dict, List
from ..schemas import BaseResponse, SuccessResponse, ErrorResponse, MetaInfo, ErrorDetail


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


def create_meta_info(
    request_id: Optional[str] = None,
    pagination: Optional[Dict[str, Any]] = None
) -> MetaInfo:
    """Create metadata for API responses."""
    meta_data = {
        "requestId": request_id or generate_request_id(),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    # Only include pagination if it's provided
    if pagination is not None:
        meta_data["pagination"] = pagination
    
    return MetaInfo(**meta_data)


def create_success_response(
    data: Any = None,
    code: int = 200,
    request_id: Optional[str] = None,
    pagination: Optional[Dict[str, Any]] = None
) -> SuccessResponse:
    """Create a standardized success response."""
    return SuccessResponse(
        status="success",
        code=code,
        data=data,
        meta=create_meta_info(request_id, pagination)
    )


def create_error_response(
    message: str,
    code: int = 400,
    errors: Optional[List[ErrorDetail]] = None,
    request_id: Optional[str] = None
) -> ErrorResponse:
    """Create a standardized error response."""
    return ErrorResponse(
        status="error",
        code=code,
        message=message,
        errors=errors,
        meta=create_meta_info(request_id)
    )


def raise_http_exception(
    message: str,
    status_code: int = 400,
    errors: Optional[List[ErrorDetail]] = None,
    request_id: Optional[str] = None
) -> None:
    """Raise a standardized HTTP exception."""
    error_response = create_error_response(
        message=message,
        code=status_code,
        errors=errors,
        request_id=request_id
    )
    raise HTTPException(
        status_code=status_code,
        detail=error_response.model_dump(exclude_none=True)
    )


# Common error responses
def raise_validation_error(
    message: str, 
    errors: Optional[List[ErrorDetail]] = None,
    request_id: Optional[str] = None
) -> None:
    """Raise a validation error."""
    raise_http_exception(
        message=message,
        status_code=status.HTTP_400_BAD_REQUEST,
        errors=errors,
        request_id=request_id
    )


def raise_authentication_error(
    message: str = "Authentication failed",
    request_id: Optional[str] = None
) -> None:
    """Raise an authentication error."""
    raise_http_exception(
        message=message,
        status_code=status.HTTP_401_UNAUTHORIZED,
        request_id=request_id
    )


def raise_authorization_error(
    message: str = "Access denied",
    request_id: Optional[str] = None
) -> None:
    """Raise an authorization error."""
    raise_http_exception(
        message=message,
        status_code=status.HTTP_403_FORBIDDEN,
        request_id=request_id
    )


def raise_not_found_error(
    message: str = "Resource not found",
    request_id: Optional[str] = None
) -> None:
    """Raise a not found error."""
    raise_http_exception(
        message=message,
        status_code=status.HTTP_404_NOT_FOUND,
        request_id=request_id
    )


def raise_rate_limit_error(
    message: str = "Rate limit exceeded",
    request_id: Optional[str] = None
) -> None:
    """Raise a rate limit error."""
    raise_http_exception(
        message=message,
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        request_id=request_id
    )


def raise_server_error(
    message: str = "Internal server error",
    request_id: Optional[str] = None
) -> None:
    """Raise a server error."""
    raise_http_exception(
        message=message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=request_id
    )
