"""
Operator-related background tasks.
"""
import logging
from typing import Optional
from celery import Task
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import Operator, OperatorUser
from ..services.email_service import SESEmailService
from .celery_app import celery_app

logger = logging.getLogger(__name__)

# Initialize email service
email_service = SESEmailService()


class CallbackTask(Task):
    """Base task class with error handling and logging."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Operator task {task_id} failed: {exc}")
        super().on_failure(exc, task_id, args, kwargs, einfo)
    
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Operator task {task_id} completed successfully")


@celery_app.task(bind=True, base=CallbackTask, max_retries=3)
def send_operator_notification(self, operator_id: int, notification_type: str, 
                             data: Optional[dict] = None):
    """
    Send notification to operator.
    
    Args:
        operator_id: Operator ID
        notification_type: Type of notification
        data: Additional data for the notification
    """
    db = SessionLocal()
    try:
        operator = db.query(Operator).filter(Operator.id == operator_id).first()
        if not operator:
            logger.error(f"Operator {operator_id} not found")
            return
        
        if notification_type == "account_created":
            # Send account creation notification
            message_id = email_service.send_simple_email(
                to_email=operator.contact_email,
                subject="Your BlueBus Plus account has been created",
                html_body=f"""
                <html>
                <body>
                    <h2>Account Created Successfully</h2>
                    <p>Hello {operator.company_name},</p>
                    <p>Your BlueBus Plus account has been created successfully.</p>
                    <p>You can now start uploading your documents and complete the verification process.</p>
                    <p>If you have any questions, please contact our support team.</p>
                </body>
                </html>
                """,
                text_body=f"""
                Account Created Successfully
                
                Hello {operator.company_name},
                
                Your BlueBus Plus account has been created successfully.
                
                You can now start uploading your documents and complete the verification process.
                
                If you have any questions, please contact our support team.
                """
            )
            
        elif notification_type == "account_suspended":
            # Send account suspension notification
            reason = data.get("reason", "Policy violation") if data else "Policy violation"
            message_id = email_service.send_simple_email(
                to_email=operator.contact_email,
                subject="Your BlueBus Plus account has been suspended",
                html_body=f"""
                <html>
                <body>
                    <h2>Account Suspended</h2>
                    <p>Hello {operator.company_name},</p>
                    <p>Your BlueBus Plus account has been suspended.</p>
                    <p>Reason: {reason}</p>
                    <p>Please contact our support team for more information.</p>
                </body>
                </html>
                """,
                text_body=f"""
                Account Suspended
                
                Hello {operator.company_name},
                
                Your BlueBus Plus account has been suspended.
                
                Reason: {reason}
                
                Please contact our support team for more information.
                """
            )
            
        elif notification_type == "document_expiring":
            # Send document expiration warning
            doc_type = data.get("doc_type", "document") if data else "document"
            days_until_expiry = data.get("days_until_expiry", 30) if data else 30
            
            message_id = email_service.send_simple_email(
                to_email=operator.contact_email,
                subject=f"Document expiration warning - {doc_type}",
                html_body=f"""
                <html>
                <body>
                    <h2>Document Expiration Warning</h2>
                    <p>Hello {operator.company_name},</p>
                    <p>Your {doc_type} document will expire in {days_until_expiry} days.</p>
                    <p>Please upload a new document to maintain your account status.</p>
                </body>
                </html>
                """,
                text_body=f"""
                Document Expiration Warning
                
                Hello {operator.company_name},
                
                Your {doc_type} document will expire in {days_until_expiry} days.
                
                Please upload a new document to maintain your account status.
                """
            )
            
        else:
            logger.warning(f"Unknown notification type: {notification_type}")
            return
        
        logger.info(f"Notification {notification_type} sent to operator {operator_id}")
        
    except Exception as e:
        logger.error(f"Error sending notification to operator {operator_id}: {e}")
        raise self.retry(exc=e, countdown=60)
    
    finally:
        db.close()


@celery_app.task(bind=True, base=CallbackTask, max_retries=3)
def check_expiring_documents(self):
    """
    Check for documents that are expiring soon and send notifications.
    """
    db = SessionLocal()
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import and_
        
        # Check for documents expiring in the next 30 days
        expiry_threshold = datetime.utcnow() + timedelta(days=30)
        
        expiring_docs = db.query(OperatorDocument).filter(
            and_(
                OperatorDocument.expiry_date <= expiry_threshold,
                OperatorDocument.expiry_date > datetime.utcnow(),
                OperatorDocument.status == "VERIFIED"
            )
        ).all()
        
        for doc in expiring_docs:
            # Calculate days until expiry
            days_until_expiry = (doc.expiry_date - datetime.utcnow()).days
            
            # Send notification
            send_operator_notification.delay(
                operator_id=doc.operator_id,
                notification_type="document_expiring",
                data={
                    "doc_type": doc.doc_type,
                    "days_until_expiry": days_until_expiry
                }
            )
        
        logger.info(f"Checked {len(expiring_docs)} expiring documents")
        
    except Exception as e:
        logger.error(f"Error checking expiring documents: {e}")
        raise self.retry(exc=e, countdown=60)
    
    finally:
        db.close()


@celery_app.task(bind=True, base=CallbackTask, max_retries=3)
def cleanup_inactive_operators(self):
    """
    Clean up inactive operators and their data.
    """
    db = SessionLocal()
    try:
        from datetime import datetime, timedelta
        
        # Find operators that have been inactive for more than 90 days
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        inactive_operators = db.query(Operator).filter(
            and_(
                Operator.status == "PENDING",
                Operator.created_at < cutoff_date
            )
        ).all()
        
        for operator in inactive_operators:
            # Send final notification
            send_operator_notification.delay(
                operator_id=operator.id,
                notification_type="account_cleanup",
                data={"days_inactive": 90}
            )
            
            # Mark as rejected
            operator.status = "REJECTED"
            operator.verification_notes = "Account closed due to inactivity"
        
        db.commit()
        
        logger.info(f"Cleaned up {len(inactive_operators)} inactive operators")
        
    except Exception as e:
        logger.error(f"Error cleaning up inactive operators: {e}")
        raise self.retry(exc=e, countdown=60)
    
    finally:
        db.close()


@celery_app.task(bind=True, base=CallbackTask, max_retries=3)
def send_operator_activation_email(self, operator_id: int):
    """
    Send operator activation email (alias for email task).
    
    Args:
        operator_id: Operator ID
    """
    from .email_tasks import send_operator_activation_email as email_task
    return email_task.delay(operator_id)
