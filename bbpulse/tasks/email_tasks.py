"""
Email-related background tasks.
"""
import logging
from typing import Optional
from celery import Task
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import Operator, OperatorUser, EmailLog
from ..services.email_service import SESEmailService
from .celery_app import celery_app

logger = logging.getLogger(__name__)

# Initialize email service
email_service = SESEmailService()


class CallbackTask(Task):
    """Base task class with error handling and logging."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Email task {task_id} failed: {exc}")
        super().on_failure(exc, task_id, args, kwargs, einfo)
    
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Email task {task_id} completed successfully")


@celery_app.task(bind=True, base=CallbackTask, max_retries=3)
def send_operator_activation_email(self, operator_id: int):
    """
    Send operator activation email.
    
    Args:
        operator_id: Operator ID
    """
    db = SessionLocal()
    try:
        operator = db.query(Operator).filter(Operator.id == operator_id).first()
        if not operator:
            logger.error(f"Operator {operator_id} not found")
            return
        
        # Generate activation link (in real implementation, this would be a proper URL)
        activation_link = f"https://app.blubus.com/activate/{operator_id}"
        
        # Send activation email
        message_id = email_service.send_operator_activation_email(
            operator_email=operator.contact_email,
            operator_name=operator.company_name,
            activation_link=activation_link,
            operator_id=operator_id
        )
        
        # Log email in database
        email_log = EmailLog(
            operator_id=operator_id,
            template_name="operator_activation",
            recipient_email=operator.contact_email,
            subject="Your BlueBus Plus account has been activated",
            status="SENT",
            ses_message_id=message_id
        )
        db.add(email_log)
        db.commit()
        
        logger.info(f"Activation email sent to operator {operator_id}")
        
    except Exception as e:
        logger.error(f"Error sending activation email to operator {operator_id}: {e}")
        raise self.retry(exc=e, countdown=60)
    
    finally:
        db.close()


@celery_app.task(bind=True, base=CallbackTask, max_retries=3)
def send_document_verification_email(self, operator_id: int, doc_type: str, 
                                   status: str, notes: Optional[str] = None):
    """
    Send document verification status email.
    
    Args:
        operator_id: Operator ID
        doc_type: Type of document
        status: Verification status
        notes: Additional notes
    """
    db = SessionLocal()
    try:
        operator = db.query(Operator).filter(Operator.id == operator_id).first()
        if not operator:
            logger.error(f"Operator {operator_id} not found")
            return
        
        # Send verification email
        message_id = email_service.send_document_verification_email(
            operator_email=operator.contact_email,
            operator_name=operator.company_name,
            doc_type=doc_type,
            status=status,
            notes=notes,
            operator_id=operator_id
        )
        
        # Log email in database
        email_log = EmailLog(
            operator_id=operator_id,
            template_name="document_verification",
            recipient_email=operator.contact_email,
            subject=f"Document verification update - {doc_type}",
            status="SENT",
            ses_message_id=message_id
        )
        db.add(email_log)
        db.commit()
        
        logger.info(f"Document verification email sent to operator {operator_id}")
        
    except Exception as e:
        logger.error(f"Error sending document verification email to operator {operator_id}: {e}")
        raise self.retry(exc=e, countdown=60)
    
    finally:
        db.close()


@celery_app.task(bind=True, base=CallbackTask, max_retries=3)
def send_password_reset_email(self, user_email: str, reset_token: str):
    """
    Send password reset email.
    
    Args:
        user_email: User's email address
        reset_token: Password reset token
    """
    try:
        # Generate reset link
        reset_link = f"https://app.blubus.com/reset-password?token={reset_token}"
        
        # Send password reset email
        message_id = email_service.send_simple_email(
            to_email=user_email,
            subject="Reset your BlueBus Plus password",
            html_body=f"""
            <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>You have requested to reset your password for BlueBus Plus.</p>
                <p>Click the link below to reset your password:</p>
                <a href="{reset_link}">Reset Password</a>
                <p>This link will expire in 24 hours.</p>
                <p>If you didn't request this, please ignore this email.</p>
            </body>
            </html>
            """,
            text_body=f"""
            Password Reset Request
            
            You have requested to reset your password for BlueBus Plus.
            
            Click the link below to reset your password:
            {reset_link}
            
            This link will expire in 24 hours.
            
            If you didn't request this, please ignore this email.
            """
        )
        
        logger.info(f"Password reset email sent to {user_email}")
        
    except Exception as e:
        logger.error(f"Error sending password reset email to {user_email}: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, base=CallbackTask, max_retries=3)
def send_welcome_email(self, user_id: int):
    """
    Send welcome email to new user.
    
    Args:
        user_id: User ID
    """
    db = SessionLocal()
    try:
        user = db.query(OperatorUser).filter(OperatorUser.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found")
            return
        
        operator = db.query(Operator).filter(Operator.id == user.operator_id).first()
        if not operator:
            logger.error(f"Operator {user.operator_id} not found")
            return
        
        # Send welcome email
        message_id = email_service.send_simple_email(
            to_email=user.email,
            subject="Welcome to BlueBus Plus",
            html_body=f"""
            <html>
            <body>
                <h2>Welcome to BlueBus Plus!</h2>
                <p>Hello {user.first_name or 'there'},</p>
                <p>Welcome to BlueBus Plus for {operator.company_name}!</p>
                <p>Your account has been created successfully. You can now:</p>
                <ul>
                    <li>Upload and manage documents</li>
                    <li>Track your application status</li>
                    <li>Access your operator dashboard</li>
                </ul>
                <p>If you have any questions, please contact our support team.</p>
            </body>
            </html>
            """,
            text_body=f"""
            Welcome to BlueBus Plus!
            
            Hello {user.first_name or 'there'},
            
            Welcome to BlueBus Plus for {operator.company_name}!
            
            Your account has been created successfully. You can now:
            - Upload and manage documents
            - Track your application status
            - Access your operator dashboard
            
            If you have any questions, please contact our support team.
            """
        )
        
        # Log email in database
        email_log = EmailLog(
            operator_id=user.operator_id,
            template_name="welcome_email",
            recipient_email=user.email,
            subject="Welcome to BlueBus Plus",
            status="SENT",
            ses_message_id=message_id
        )
        db.add(email_log)
        db.commit()
        
        logger.info(f"Welcome email sent to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error sending welcome email to user {user_id}: {e}")
        raise self.retry(exc=e, countdown=60)
    
    finally:
        db.close()


@celery_app.task(bind=True, base=CallbackTask, max_retries=3)
def process_ses_bounce(self, bounce_data: dict):
    """
    Process SES bounce/complaint notifications.
    
    Args:
        bounce_data: Bounce notification data from SNS
    """
    db = SessionLocal()
    try:
        # Extract message ID from bounce data
        message_id = bounce_data.get("mail", {}).get("messageId")
        if not message_id:
            logger.error("No message ID in bounce data")
            return
        
        # Find email log entry
        email_log = db.query(EmailLog).filter(
            EmailLog.ses_message_id == message_id
        ).first()
        
        if not email_log:
            logger.warning(f"No email log found for message ID: {message_id}")
            return
        
        # Update email status
        bounce_type = bounce_data.get("bounce", {}).get("bounceType", "unknown")
        email_log.status = "BOUNCED"
        email_log.bounced_at = "2024-01-01T00:00:00Z"  # Use actual timestamp
        email_log.error_message = f"Bounce type: {bounce_type}"
        
        db.commit()
        
        logger.info(f"Processed bounce for message {message_id}")
        
    except Exception as e:
        logger.error(f"Error processing SES bounce: {e}")
        raise self.retry(exc=e, countdown=60)
    
    finally:
        db.close()


@celery_app.task(bind=True, base=CallbackTask, max_retries=3)
def process_ses_complaint(self, complaint_data: dict):
    """
    Process SES complaint notifications.
    
    Args:
        complaint_data: Complaint notification data from SNS
    """
    db = SessionLocal()
    try:
        # Extract message ID from complaint data
        message_id = complaint_data.get("mail", {}).get("messageId")
        if not message_id:
            logger.error("No message ID in complaint data")
            return
        
        # Find email log entry
        email_log = db.query(EmailLog).filter(
            EmailLog.ses_message_id == message_id
        ).first()
        
        if not email_log:
            logger.warning(f"No email log found for message ID: {message_id}")
            return
        
        # Update email status
        email_log.status = "COMPLAINED"
        email_log.error_message = "Email marked as spam by recipient"
        
        db.commit()
        
        logger.info(f"Processed complaint for message {message_id}")
        
    except Exception as e:
        logger.error(f"Error processing SES complaint: {e}")
        raise self.retry(exc=e, countdown=60)
    
    finally:
        db.close()

