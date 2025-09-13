"""
SES email service for sending transactional emails.
"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from .aws_service import AWSService
from ..settings import settings

logger = logging.getLogger(__name__)


class SESEmailService(AWSService):
    """Service for sending emails via AWS SES."""
    
    def __init__(self):
        super().__init__()
        self.source_email = settings.ses_source_email
        self.reply_to_email = settings.ses_reply_to_email
    
    def send_templated_email(self, to_email: str, template_name: str, 
                           template_data: Dict[str, Any], 
                           operator_id: Optional[int] = None) -> str:
        """
        Send templated email via SES.
        
        Args:
            to_email: Recipient email address
            template_name: Name of the SES template
            template_data: Data to populate template variables
            operator_id: Optional operator ID for logging
            
        Returns:
            SES message ID
        """
        try:
            response = self.ses_client.send_templated_email(
                Source=self.source_email,
                Destination={'ToAddresses': [to_email]},
                Template=template_name,
                TemplateData=json.dumps(template_data),
                ReplyToAddresses=[self.reply_to_email] if self.reply_to_email else None
            )
            
            message_id = response['MessageId']
            logger.info(f"Sent templated email {template_name} to {to_email}, MessageId: {message_id}")
            
            # Log email in database
            self._log_email(operator_id, template_name, to_email, 
                          f"Template: {template_name}", message_id)
            
            return message_id
            
        except Exception as e:
            logger.error(f"Failed to send templated email to {to_email}: {e}")
            raise
    
    def send_simple_email(self, to_email: str, subject: str, 
                         html_body: str, text_body: Optional[str] = None,
                         operator_id: Optional[int] = None) -> str:
        """
        Send simple email via SES.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body (optional)
            operator_id: Optional operator ID for logging
            
        Returns:
            SES message ID
        """
        try:
            message = {
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Html': {'Data': html_body, 'Charset': 'UTF-8'}
                }
            }
            
            if text_body:
                message['Body']['Text'] = {'Data': text_body, 'Charset': 'UTF-8'}
            
            response = self.ses_client.send_email(
                Source=self.source_email,
                Destination={'ToAddresses': [to_email]},
                Message=message,
                ReplyToAddresses=[self.reply_to_email] if self.reply_to_email else None
            )
            
            message_id = response['MessageId']
            logger.info(f"Sent simple email to {to_email}, MessageId: {message_id}")
            
            # Log email in database
            self._log_email(operator_id, None, to_email, subject, message_id)
            
            return message_id
            
        except Exception as e:
            logger.error(f"Failed to send simple email to {to_email}: {e}")
            raise
    
    def create_email_template(self, template_name: str, subject: str, 
                            html_template: str, text_template: Optional[str] = None,
                            variables: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create SES email template.
        
        Args:
            template_name: Name of the template
            subject: Email subject template
            html_template: HTML template content
            text_template: Plain text template content
            variables: Template variables schema
            
        Returns:
            True if successful, False otherwise
        """
        try:
            template_data = {
                'TemplateName': template_name,
                'SubjectPart': subject,
                'HtmlPart': html_template
            }
            
            if text_template:
                template_data['TextPart'] = text_template
            
            self.ses_client.create_template(Template=template_data)
            logger.info(f"Created email template: {template_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create email template {template_name}: {e}")
            return False
    
    def update_email_template(self, template_name: str, subject: str, 
                            html_template: str, text_template: Optional[str] = None) -> bool:
        """
        Update existing SES email template.
        
        Args:
            template_name: Name of the template
            subject: Email subject template
            html_template: HTML template content
            text_template: Plain text template content
            
        Returns:
            True if successful, False otherwise
        """
        try:
            template_data = {
                'TemplateName': template_name,
                'SubjectPart': subject,
                'HtmlPart': html_template
            }
            
            if text_template:
                template_data['TextPart'] = text_template
            
            self.ses_client.update_template(Template=template_data)
            logger.info(f"Updated email template: {template_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update email template {template_name}: {e}")
            return False
    
    def delete_email_template(self, template_name: str) -> bool:
        """
        Delete SES email template.
        
        Args:
            template_name: Name of the template
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.ses_client.delete_template(TemplateName=template_name)
            logger.info(f"Deleted email template: {template_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete email template {template_name}: {e}")
            return False
    
    def list_email_templates(self) -> List[Dict[str, Any]]:
        """
        List all SES email templates.
        
        Returns:
            List of template information
        """
        try:
            response = self.ses_client.list_templates()
            return response.get('TemplatesMetadata', [])
            
        except Exception as e:
            logger.error(f"Failed to list email templates: {e}")
            raise
    
    def get_send_quota(self) -> Dict[str, Any]:
        """
        Get SES sending quota information.
        
        Returns:
            Dictionary containing quota information
        """
        try:
            response = self.ses_client.get_send_quota()
            return response
            
        except Exception as e:
            logger.error(f"Failed to get send quota: {e}")
            raise
    
    def verify_email_identity(self, email: str) -> bool:
        """
        Verify email identity in SES.
        
        Args:
            email: Email address to verify
            
        Returns:
            True if verification request sent, False otherwise
        """
        try:
            self.ses_client.verify_email_identity(EmailAddress=email)
            logger.info(f"Verification email sent to: {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to verify email identity {email}: {e}")
            return False
    
    def _log_email(self, operator_id: Optional[int], template_name: Optional[str], 
                   recipient_email: str, subject: str, message_id: str):
        """
        Log email in database for tracking.
        
        Args:
            operator_id: Optional operator ID
            template_name: Name of the template used
            recipient_email: Recipient email address
            subject: Email subject
            message_id: SES message ID
        """
        try:
            # This would typically insert into the EmailLog table
            # For now, we'll just log it
            logger.info(f"Email logged - Operator: {operator_id}, Template: {template_name}, "
                       f"Recipient: {recipient_email}, Subject: {subject}, MessageId: {message_id}")
            
        except Exception as e:
            logger.error(f"Failed to log email: {e}")
    
    def send_operator_activation_email(self, operator_email: str, operator_name: str, 
                                     activation_link: str, operator_id: int) -> str:
        """
        Send operator activation email.
        
        Args:
            operator_email: Operator's email address
            operator_name: Operator's company name
            activation_link: Activation link
            operator_id: Operator ID
            
        Returns:
            SES message ID
        """
        template_data = {
            "operator_name": operator_name,
            "activation_link": activation_link
        }
        
        return self.send_templated_email(
            to_email=operator_email,
            template_name="operator_activation",
            template_data=template_data,
            operator_id=operator_id
        )
    
    def send_document_verification_email(self, operator_email: str, operator_name: str,
                                       doc_type: str, status: str, notes: Optional[str],
                                       operator_id: int) -> str:
        """
        Send document verification status email.
        
        Args:
            operator_email: Operator's email address
            operator_name: Operator's company name
            doc_type: Type of document
            status: Verification status
            notes: Additional notes
            operator_id: Operator ID
            
        Returns:
            SES message ID
        """
        template_data = {
            "operator_name": operator_name,
            "doc_type": doc_type,
            "status": status,
            "notes": notes or ""
        }
        
        return self.send_templated_email(
            to_email=operator_email,
            template_name="document_verification",
            template_data=template_data,
            operator_id=operator_id
        )
