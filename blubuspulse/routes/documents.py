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
    OperatorDocument, OperatorDocumentUpdate
)
from ..auth.dependencies import get_current_user
from ..services.s3_service import S3DocumentService
from ..tasks.document_processing import process_document_upload, delete_document_from_s3
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])
s3_service = S3DocumentService()


@router.post("/operators/{operator_id}/upload-url", response_model=PresignResponse)
async def generate_upload_url(
    operator_id: int,
    request: DocumentUploadRequest,
    db: Session = Depends(get_db),
    current_user: OperatorUser = Depends(get_current_user)
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
    current_user: OperatorUser = Depends(get_current_user)
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


@router.get("/operators/{operator_id}", response_model=List[OperatorDocument])
async def list_operator_documents(
    operator_id: int,
    doc_type: Optional[str] = Query(None, description="Filter by document type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: OperatorUser = Depends(get_current_user)
):
    """List documents for an operator."""
    # Check if user has access to this operator
    if current_user.operator_id != operator_id and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    query = db.query(OperatorDocument).filter(OperatorDocument.operator_id == operator_id)
    
    if doc_type:
        query = query.filter(OperatorDocument.doc_type == doc_type)
    
    if status:
        query = query.filter(OperatorDocument.status == status)
    
    documents = query.order_by(OperatorDocument.uploaded_at.desc()).all()
    return documents


@router.get("/{document_id}", response_model=OperatorDocument)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: OperatorUser = Depends(get_current_user)
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
    current_user: OperatorUser = Depends(get_current_user)
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
    current_user: OperatorUser = Depends(get_current_user)
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
    current_user: OperatorUser = Depends(get_current_user)
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


@router.get("/operators/{operator_id}/required", response_model=List[dict])
async def get_required_documents(
    operator_id: int,
    db: Session = Depends(get_db),
    current_user: OperatorUser = Depends(get_current_user)
):
    """Get list of required documents for operator."""
    # Check if user has access to this operator
    if current_user.operator_id != operator_id and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
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
    
    return required_docs
