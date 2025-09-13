"""
Document processing background tasks.
"""
import tempfile
import logging
from typing import Dict, Any, Optional
from celery import Task
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import OperatorDocument, Operator
from ..services.s3_service import S3DocumentService
from ..services.email_service import SESEmailService
from .celery_app import celery_app

logger = logging.getLogger(__name__)

# Initialize services
s3_service = S3DocumentService()
email_service = SESEmailService()


class CallbackTask(Task):
    """Base task class with error handling and logging."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {task_id} failed: {exc}")
        super().on_failure(exc, task_id, args, kwargs, einfo)
    
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Task {task_id} completed successfully")


@celery_app.task(bind=True, base=CallbackTask, max_retries=3)
def process_document_upload(self, doc_id: int):
    """
    Process uploaded document (OCR, verification, etc.).
    
    Args:
        doc_id: Document ID to process
    """
    db = SessionLocal()
    try:
        # Get document from database
        document = db.query(OperatorDocument).filter(OperatorDocument.id == doc_id).first()
        if not document:
            logger.error(f"Document {doc_id} not found")
            return
        
        # Get operator information
        operator = db.query(Operator).filter(Operator.id == document.operator_id).first()
        if not operator:
            logger.error(f"Operator {document.operator_id} not found")
            return
        
        logger.info(f"Processing document {doc_id} for operator {operator.company_name}")
        
        # Check if document exists in S3
        if not s3_service.check_document_exists(document.file_key):
            logger.error(f"Document {document.file_key} not found in S3")
            document.status = "REJECTED"
            document.verification_notes = "Document not found in S3"
            db.commit()
            return
        
        # Get document metadata from S3
        try:
            metadata = s3_service.get_document_metadata(document.file_key)
            document.file_size = metadata.get("content_length")
            document.content_type = metadata.get("content_type")
        except Exception as e:
            logger.warning(f"Failed to get document metadata: {e}")
        
        # Simulate document processing (OCR, verification, etc.)
        # In a real implementation, you would:
        # 1. Download document from S3
        # 2. Run OCR on the document
        # 3. Verify document content against business rules
        # 4. Update document status and metadata
        
        # For now, we'll simulate successful processing
        document.status = "VERIFIED"
        document.verification_notes = "Document processed successfully"
        document.metadata = {
            "processed_at": "2024-01-01T00:00:00Z",
            "ocr_text": "Sample OCR text extracted from document",
            "verification_score": 0.95,
            "file_size": document.file_size
        }
        
        db.commit()
        
        # Send verification email to operator
        send_document_verification_email.delay(
            operator_id=operator.id,
            doc_type=document.doc_type,
            status="VERIFIED",
            notes="Document has been successfully verified"
        )
        
        # Check if all required documents are verified
        check_operator_documents.delay(operator.id)
        
        logger.info(f"Document {doc_id} processed successfully")
        
    except Exception as e:
        logger.error(f"Error processing document {doc_id}: {e}")
        # Update document status to rejected
        if 'document' in locals():
            document.status = "REJECTED"
            document.verification_notes = f"Processing failed: {str(e)}"
            db.commit()
        raise self.retry(exc=e, countdown=60)
    
    finally:
        db.close()


@celery_app.task(bind=True, base=CallbackTask, max_retries=3)
def check_operator_documents(self, operator_id: int):
    """
    Check if all required documents for an operator are verified.
    
    Args:
        operator_id: Operator ID to check
    """
    db = SessionLocal()
    try:
        operator = db.query(Operator).filter(Operator.id == operator_id).first()
        if not operator:
            logger.error(f"Operator {operator_id} not found")
            return
        
        # Get all documents for the operator
        documents = db.query(OperatorDocument).filter(
            OperatorDocument.operator_id == operator_id
        ).all()
        
        # Define required document types
        required_doc_types = ["RC", "PERMIT", "INSURANCE", "TAX_CERTIFICATE"]
        
        # Check if all required documents are verified
        verified_doc_types = set()
        for doc in documents:
            if doc.status == "VERIFIED":
                verified_doc_types.add(doc.doc_type)
        
        missing_doc_types = set(required_doc_types) - verified_doc_types
        
        if not missing_doc_types:
            # All required documents are verified
            if operator.status != "ACTIVE":
                operator.status = "ACTIVE"
                operator.verified_at = "2024-01-01T00:00:00Z"  # Use actual timestamp
                db.commit()
                
                # Send activation email
                send_operator_activation_email.delay(operator.id)
                
                logger.info(f"Operator {operator_id} activated - all documents verified")
        else:
            logger.info(f"Operator {operator_id} still missing documents: {missing_doc_types}")
        
    except Exception as e:
        logger.error(f"Error checking operator documents for {operator_id}: {e}")
        raise self.retry(exc=e, countdown=60)
    
    finally:
        db.close()


@celery_app.task(bind=True, base=CallbackTask, max_retries=3)
def delete_document_from_s3(self, file_key: str):
    """
    Delete document from S3.
    
    Args:
        file_key: S3 object key to delete
    """
    try:
        success = s3_service.delete_document(file_key)
        if success:
            logger.info(f"Document {file_key} deleted from S3")
        else:
            logger.error(f"Failed to delete document {file_key} from S3")
            raise Exception("Failed to delete document from S3")
    
    except Exception as e:
        logger.error(f"Error deleting document {file_key}: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, base=CallbackTask, max_retries=3)
def generate_document_thumbnail(self, doc_id: int):
    """
    Generate thumbnail for document.
    
    Args:
        doc_id: Document ID
    """
    db = SessionLocal()
    try:
        document = db.query(OperatorDocument).filter(OperatorDocument.id == doc_id).first()
        if not document:
            logger.error(f"Document {doc_id} not found")
            return
        
        # In a real implementation, you would:
        # 1. Download document from S3
        # 2. Generate thumbnail
        # 3. Upload thumbnail to S3
        # 4. Update document metadata with thumbnail URL
        
        logger.info(f"Thumbnail generation for document {doc_id} completed")
        
    except Exception as e:
        logger.error(f"Error generating thumbnail for document {doc_id}: {e}")
        raise self.retry(exc=e, countdown=60)
    
    finally:
        db.close()
