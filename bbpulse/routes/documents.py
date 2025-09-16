"""
Document management API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from ..database import get_db
from ..models import Operator, OperatorDocument, OperatorUser
from ..schemas import (
    DocumentUploadRequest, PresignResponse, DocumentRegisterRequest,
    OperatorDocument, OperatorDocumentUpdate, DocumentsListResponse,
    RequiredDocumentsListResponse
)
from ..auth.dependencies import get_current_user, get_current_operator_user
from ..services.s3_service import S3DocumentService
from ..tasks.document_processing import process_document_upload, delete_document_from_s3
from ..utils.response_utils import (
    create_success_response, raise_validation_error, raise_authorization_error,
    raise_server_error
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])
s3_service = S3DocumentService()


@router.post("/operators/{operator_id}/upload-url", response_model=PresignResponse)
async def generate_upload_url(
    operator_id: int,
    request: DocumentUploadRequest,
    db: Session = Depends(get_db),
    current_user: OperatorUser = Depends(get_current_operator_user)
):
    """Generate presigned URL for document upload."""
    # Check if user has access to this operator
    if current_user.operator_id != operator_id and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if operator exists
    operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operator not found"
        )
    
    try:
        # Generate presigned POST URL
        presigned_data = s3_service.generate_presigned_post(
            operator_id=str(operator_id),
            filename=request.filename,
            content_type=request.content_type,
            doc_type=request.doc_type
        )
        
        logger.info(f"Generated upload URL for operator {operator_id}, doc_type: {request.doc_type}")
        return presigned_data
        
    except Exception as e:
        logger.error(f"Error generating upload URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate upload URL"
        )


@router.post("/operators/{operator_id}/register", response_model=OperatorDocument, status_code=status.HTTP_201_CREATED)
async def register_document(
    operator_id: int,
    document_data: DocumentRegisterRequest,
    db: Session = Depends(get_db),
    current_user: OperatorUser = Depends(get_current_operator_user)
):
    """Register uploaded document in database."""
    # Check if user has access to this operator
    if current_user.operator_id != operator_id and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if operator exists
    operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operator not found"
        )
    
    # Check if document exists in S3
    if not s3_service.check_document_exists(document_data.file_key):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document not found in S3"
        )
    
    try:
        # Get document metadata from S3
        metadata = s3_service.get_document_metadata(document_data.file_key)
        
        # Create document record
        document = OperatorDocument(
            operator_id=operator_id,
            doc_type=document_data.doc_type,
            file_key=document_data.file_key,
            file_name=document_data.file_key.split('/')[-1],  # Extract filename
            file_size=metadata.get("content_length"),
            content_type=metadata.get("content_type"),
            expiry_date=document_data.expiry_date,
            uploaded_by=document_data.uploaded_by or current_user.email,
            status="UPLOADED"
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Start document processing task
        process_document_upload.delay(document.id)
        
        logger.info(f"Registered document {document.id} for operator {operator_id}")
        return document
        
    except Exception as e:
        logger.error(f"Error registering document: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register document"
        )


@router.get(
    "/operators/{operator_id}", 
    response_model=DocumentsListResponse,
    responses={
        200: {
            "description": "List of operator documents retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "code": 200,
                        "data": [
                            {
                                "id": 1,
                                "operator_id": 12,
                                "doc_type": "BUSINESS_LICENSE",
                                "file_name": "business_license.pdf",
                                "file_size": 1024000,
                                "content_type": "application/pdf",
                                "file_key": "documents/12/business_license_20240116.pdf",
                                "status": "VERIFIED",
                                "uploaded_at": "2024-01-16T10:00:00Z",
                                "verified_at": "2024-01-16T10:30:00Z",
                                "expiry_date": "2025-01-16T10:00:00Z",
                                "uploaded_by": "admin@example.com"
                            },
                            {
                                "id": 2,
                                "operator_id": 12,
                                "doc_type": "INSURANCE_CERTIFICATE",
                                "file_name": "insurance_cert.pdf",
                                "file_size": 512000,
                                "content_type": "application/pdf",
                                "file_key": "documents/12/insurance_cert_20240116.pdf",
                                "status": "PENDING",
                                "uploaded_at": "2024-01-16T11:00:00Z",
                                "verified_at": None,
                                "expiry_date": "2025-06-16T11:00:00Z",
                                "uploaded_by": "manager@example.com"
                            }
                        ],
                        "meta": {
                            "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
                            "timestamp": "2024-01-16T10:12:02.998989+05:30",
                            "pagination": {
                                "page": 1,
                                "pageSize": 50,
                                "total": 2
                            }
                        }
                    }
                }
            }
        },
        401: {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "code": 401,
                        "message": "Authentication required",
                        "meta": {
                            "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
                            "timestamp": "2024-01-16T10:12:02.998989+05:30"
                        }
                    }
                }
            }
        },
        403: {
            "description": "Access denied",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "code": 403,
                        "message": "Access denied",
                        "meta": {
                            "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
                            "timestamp": "2024-01-16T10:12:02.998989+05:30"
                        }
                    }
                }
            }
        }
    }
)
async def list_operator_documents(
    operator_id: int,
    doc_type: Optional[str] = Query(None, description="Filter by document type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: OperatorUser = Depends(get_current_operator_user)
):
    """
    List documents for an operator.
    
    This endpoint returns a list of documents associated with a specific operator.
    It supports filtering by document type and status. Only users with access to the operator
    (same operator_id or ADMIN role) can view this list.
    
    **Path Parameters:**
    - `operator_id` (integer): The ID of the operator
    
    **Query Parameters:**
    - `doc_type` (string, optional): Filter by document type (e.g., "BUSINESS_LICENSE", "INSURANCE_CERTIFICATE")
    - `status` (string, optional): Filter by status (e.g., "PENDING", "VERIFIED", "REJECTED")
    
    **Response:**
    - `status` (string): "success"
    - `code` (integer): HTTP status code (200)
    - `data` (array): List of document objects with complete details
    - `meta` (object): Request metadata with pagination information
    
    **Example Request:**
    ```
    GET /documents/operators/12?doc_type=BUSINESS_LICENSE&status=VERIFIED
    ```
    
    **Example Success Response:**
    ```json
    {
        "status": "success",
        "code": 200,
        "data": [
            {
                "id": 1,
                "operator_id": 12,
                "doc_type": "BUSINESS_LICENSE",
                "file_name": "business_license.pdf",
                "file_size": 1024000,
                "content_type": "application/pdf",
                "file_key": "documents/12/business_license_20240116.pdf",
                "status": "VERIFIED",
                "uploaded_at": "2024-01-16T10:00:00Z",
                "verified_at": "2024-01-16T10:30:00Z",
                "expiry_date": "2025-01-16T10:00:00Z",
                "uploaded_by": "admin@example.com"
            }
        ],
        "meta": {
            "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
            "timestamp": "2024-01-16T10:12:02.998989+05:30",
            "pagination": {
                "page": 1,
                "pageSize": 50,
                "total": 1
            }
        }
    }
    ```
    """
    try:
        # Check if user has access to this operator
        if current_user.operator_id != operator_id and current_user.role != "ADMIN":
            raise_authorization_error("Access denied")
        
        query = db.query(OperatorDocument).filter(OperatorDocument.operator_id == operator_id)
        
        if doc_type:
            query = query.filter(OperatorDocument.doc_type == doc_type)
        
        if status:
            query = query.filter(OperatorDocument.status == status)
        
        documents = query.order_by(OperatorDocument.uploaded_at.desc()).all()
        
        return create_success_response(
            data=documents,
            code=200
        )
        
    except Exception as e:
        logger.error(f"Error listing operator documents: {e}")
        raise_server_error("Failed to retrieve operator documents list")


@router.get("/{document_id}", response_model=OperatorDocument)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: OperatorUser = Depends(get_current_operator_user)
):
    """Get document details."""
    document = db.query(OperatorDocument).filter(OperatorDocument.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if user has access to this document
    if current_user.operator_id != document.operator_id and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return document


@router.get("/{document_id}/download")
async def get_download_url(
    document_id: int,
    expiry: Optional[int] = Query(3600, description="URL expiry in seconds"),
    db: Session = Depends(get_db),
    current_user: OperatorUser = Depends(get_current_operator_user)
):
    """Get download URL for document."""
    document = db.query(OperatorDocument).filter(OperatorDocument.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if user has access to this document
    if current_user.operator_id != document.operator_id and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        download_url = s3_service.generate_presigned_url(
            file_key=document.file_key,
            expiry=expiry
        )
        
        return {
            "download_url": download_url,
            "expires_in": expiry,
            "file_name": document.file_name
        }
        
    except Exception as e:
        logger.error(f"Error generating download URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download URL"
        )


@router.put("/{document_id}", response_model=OperatorDocument)
async def update_document(
    document_id: int,
    document_data: OperatorDocumentUpdate,
    db: Session = Depends(get_db),
    current_user: OperatorUser = Depends(get_current_operator_user)
):
    """Update document information (admin only)."""
    document = db.query(OperatorDocument).filter(OperatorDocument.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Only admin can update documents
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    
    # Update document fields
    update_data = document_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(document, field, value)
    
    # Update verification timestamp if status changed to verified
    if document_data.status == "VERIFIED" and document.status != "VERIFIED":
        document.verified_at = datetime.utcnow()
    
    db.commit()
    db.refresh(document)
    
    logger.info(f"Updated document {document_id}")
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: OperatorUser = Depends(get_current_operator_user)
):
    """Delete document."""
    document = db.query(OperatorDocument).filter(OperatorDocument.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if user has access to this document
    if current_user.operator_id != document.operator_id and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        # Delete from S3
        delete_document_from_s3.delay(document.file_key)
        
        # Delete from database
        db.delete(document)
        db.commit()
        
        logger.info(f"Deleted document {document_id}")
        
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )


@router.get(
    "/operators/{operator_id}/required", 
    response_model=RequiredDocumentsListResponse,
    responses={
        200: {
            "description": "List of required documents retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "code": 200,
                        "data": [
                            {
                                "type": "RC",
                                "name": "Registration Certificate",
                                "required": True,
                                "status": "VERIFIED",
                                "uploaded": True
                            },
                            {
                                "type": "PERMIT",
                                "name": "Operating Permit",
                                "required": True,
                                "status": "PENDING",
                                "uploaded": True
                            },
                            {
                                "type": "INSURANCE",
                                "name": "Insurance Certificate",
                                "required": True,
                                "status": "NOT_UPLOADED",
                                "uploaded": False
                            },
                            {
                                "type": "TAX_CERTIFICATE",
                                "name": "Tax Clearance Certificate",
                                "required": True,
                                "status": "NOT_UPLOADED",
                                "uploaded": False
                            },
                            {
                                "type": "PAN_CARD",
                                "name": "PAN Card",
                                "required": False,
                                "status": "VERIFIED",
                                "uploaded": True
                            },
                            {
                                "type": "GST_CERTIFICATE",
                                "name": "GST Certificate",
                                "required": False,
                                "status": "NOT_UPLOADED",
                                "uploaded": False
                            }
                        ],
                        "meta": {
                            "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
                            "timestamp": "2024-01-16T10:12:02.998989+05:30"
                        }
                    }
                }
            }
        },
        401: {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "code": 401,
                        "message": "Authentication required",
                        "meta": {
                            "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
                            "timestamp": "2024-01-16T10:12:02.998989+05:30"
                        }
                    }
                }
            }
        },
        403: {
            "description": "Access denied",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "code": 403,
                        "message": "Access denied",
                        "meta": {
                            "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
                            "timestamp": "2024-01-16T10:12:02.998989+05:30"
                        }
                    }
                }
            }
        }
    }
)
async def get_required_documents(
    operator_id: int,
    db: Session = Depends(get_db),
    current_user: OperatorUser = Depends(get_current_operator_user)
):
    """
    Get list of required documents for operator.
    
    This endpoint returns a list of all required document types for an operator,
    along with their current status (uploaded/not uploaded, verified/pending).
    Only users with access to the operator (same operator_id or ADMIN role) can view this list.
    
    **Path Parameters:**
    - `operator_id` (integer): The ID of the operator
    
    **Response:**
    - `status` (string): "success"
    - `code` (integer): HTTP status code (200)
    - `data` (array): List of required document objects with status information
    - `meta` (object): Request metadata with requestId and timestamp
    
    **Document Object Fields:**
    - `type` (string): Document type identifier
    - `name` (string): Human-readable document name
    - `required` (boolean): Whether this document is mandatory
    - `status` (string): Current status (VERIFIED, PENDING, NOT_UPLOADED)
    - `uploaded` (boolean): Whether the document has been uploaded
    
    **Example Request:**
    ```
    GET /documents/operators/12/required
    ```
    
    **Example Success Response:**
    ```json
    {
        "status": "success",
        "code": 200,
        "data": [
            {
                "type": "RC",
                "name": "Registration Certificate",
                "required": true,
                "status": "VERIFIED",
                "uploaded": true
            },
            {
                "type": "PERMIT",
                "name": "Operating Permit",
                "required": true,
                "status": "PENDING",
                "uploaded": true
            },
            {
                "type": "INSURANCE",
                "name": "Insurance Certificate",
                "required": true,
                "status": "NOT_UPLOADED",
                "uploaded": false
            }
        ],
        "meta": {
            "requestId": "f29dbe3c-1234-4567-8901-abcdef123456",
            "timestamp": "2024-01-16T10:12:02.998989+05:30"
        }
    }
    ```
    """
    try:
        # Check if user has access to this operator
        if current_user.operator_id != operator_id and current_user.role != "ADMIN":
            raise_authorization_error("Access denied")
        
        # Define required document types
        required_docs = [
            {"type": "RC", "name": "Registration Certificate", "required": True},
            {"type": "PERMIT", "name": "Operating Permit", "required": True},
            {"type": "INSURANCE", "name": "Insurance Certificate", "required": True},
            {"type": "TAX_CERTIFICATE", "name": "Tax Clearance Certificate", "required": True},
            {"type": "PAN_CARD", "name": "PAN Card", "required": False},
            {"type": "GST_CERTIFICATE", "name": "GST Certificate", "required": False}
        ]
        
        # Get uploaded documents
        uploaded_docs = db.query(OperatorDocument).filter(
            OperatorDocument.operator_id == operator_id
        ).all()
        
        # Create status map
        doc_status = {doc.doc_type: doc.status for doc in uploaded_docs}
        
        # Add status to required docs
        for doc in required_docs:
            doc["status"] = doc_status.get(doc["type"], "NOT_UPLOADED")
            doc["uploaded"] = doc["type"] in doc_status
        
        return create_success_response(
            data=required_docs,
            code=200
        )
        
    except Exception as e:
        logger.error(f"Error getting required documents: {e}")
        raise_server_error("Failed to retrieve required documents list")

