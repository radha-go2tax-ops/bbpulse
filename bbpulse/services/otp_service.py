"""
OTP Service for handling OTP generation, storage, and delivery.
"""
import random
import string
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from ..models import OTPRecord, ContactType
from ..services.email_service import SESEmailService
from ..services.whatsapp_service import WhatsAppService
from ..settings import settings

logger = logging.getLogger(__name__)


class OTPService:
    """Service for managing OTP operations."""
    
    def __init__(self):
        self.email_service = SESEmailService()
        self.whatsapp_service = WhatsAppService()
        self.otp_length = 6
        self.otp_expiry_minutes = 5
        self.max_attempts = 3
    
    def generate_otp(self) -> str:
        """Generate a random OTP code."""
        return ''.join(random.choices(string.digits, k=self.otp_length))
    
    async def send_otp(
        self, 
        contact: str, 
        contact_type: ContactType, 
        purpose: str = "registration",
        db: Session = None
    ) -> Tuple[bool, str]:
        """
        Send OTP via email or WhatsApp.
        
        Args:
            contact: Email address or phone number
            contact_type: Type of contact (email or whatsapp)
            purpose: Purpose of OTP (registration, login, etc.)
            db: Database session
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Generate OTP
            otp_code = self.generate_otp()
            
            # Store OTP in database
            if db:
                await self._store_otp(contact, contact_type, otp_code, purpose, db)
            
            # Send OTP based on contact type
            if contact_type == ContactType.EMAIL:
                success = await self._send_email_otp(contact, otp_code, purpose)
            elif contact_type == ContactType.WHATSAPP:
                success = await self._send_whatsapp_otp(contact, otp_code, purpose)
            else:
                return False, "Invalid contact type"
            
            if success:
                logger.info(f"OTP sent successfully to {contact} via {contact_type}")
                return True, f"OTP sent to your {contact_type}"
            else:
                logger.error(f"Failed to send OTP to {contact} via {contact_type}")
                return False, f"Failed to send OTP to your {contact_type}"
                
        except Exception as e:
            logger.error(f"Error sending OTP: {e}")
            return False, "Failed to send OTP"
    
    async def verify_otp(
        self, 
        contact: str, 
        contact_type: ContactType, 
        otp: str, 
        purpose: str = "registration",
        db: Session = None
    ) -> bool:
        """
        Verify OTP code.
        
        Args:
            contact: Email address or phone number
            contact_type: Type of contact (email or whatsapp)
            otp: OTP code to verify
            purpose: Purpose of OTP
            db: Database session
            
        Returns:
            True if OTP is valid, False otherwise
        """
        try:
            if not db:
                logger.error("Database session required for OTP verification")
                return False
                
            # Get OTP record from database
            otp_record = await self._get_otp_record(contact, contact_type, purpose, db)
            
            if not otp_record:
                logger.warning(f"No OTP record found for {contact}")
                return False
            
            # Check if OTP is expired
            if datetime.utcnow() > otp_record.expires_at:
                logger.warning(f"OTP expired for {contact}")
                await self._mark_otp_used(str(otp_record.id), db)
                return False
            
            # Check if OTP is already used
            if otp_record.is_used:
                logger.warning(f"OTP already used for {contact}")
                return False
            
            # Check attempt limit
            if otp_record.attempts >= self.max_attempts:
                logger.warning(f"Max attempts exceeded for {contact}")
                await self._mark_otp_used(str(otp_record.id), db)
                return False
            
            # Verify OTP code
            if otp_record.otp_code != otp:
                # Increment attempt count
                await self._increment_otp_attempts(str(otp_record.id), db)
                logger.warning(f"Invalid OTP for {contact}")
                return False
            
            # Mark OTP as used
            await self._mark_otp_used(str(otp_record.id), db)
            logger.info(f"OTP verified successfully for {contact}")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying OTP: {e}")
            return False
    
    async def _store_otp(
        self, 
        contact: str, 
        contact_type: ContactType, 
        otp_code: str, 
        purpose: str,
        db: Session
    ) -> None:
        """Store OTP in database."""
        try:
            # Clean up any existing OTP records for this contact
            db.query(OTPRecord).filter(
                OTPRecord.contact == contact,
                OTPRecord.contact_type == contact_type,
                OTPRecord.purpose == purpose
            ).delete()
            
            # Create new OTP record
            otp_record = OTPRecord(
                contact=contact,
                contact_type=contact_type,
                otp_code=otp_code,
                purpose=purpose,
                expires_at=datetime.utcnow() + timedelta(minutes=self.otp_expiry_minutes)
            )
            
            db.add(otp_record)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error storing OTP: {e}")
            db.rollback()
            raise
    
    async def _get_otp_record(
        self, 
        contact: str, 
        contact_type: ContactType, 
        purpose: str,
        db: Session
    ) -> Optional[OTPRecord]:
        """Get OTP record from database."""
        try:
            return db.query(OTPRecord).filter(
                OTPRecord.contact == contact,
                OTPRecord.contact_type == contact_type,
                OTPRecord.purpose == purpose,
                OTPRecord.is_used == False
            ).first()
        except Exception as e:
            logger.error(f"Error getting OTP record: {e}")
            return None
    
    async def _mark_otp_used(self, otp_id: str, db: Session) -> None:
        """Mark OTP as used in database."""
        try:
            otp_record = db.query(OTPRecord).filter(OTPRecord.id == otp_id).first()
            if otp_record:
                otp_record.is_used = True
                db.commit()
        except Exception as e:
            logger.error(f"Error marking OTP as used: {e}")
            db.rollback()
    
    async def _increment_otp_attempts(self, otp_id: str, db: Session) -> None:
        """Increment OTP attempt count in database."""
        try:
            otp_record = db.query(OTPRecord).filter(OTPRecord.id == otp_id).first()
            if otp_record:
                otp_record.attempts += 1
                db.commit()
        except Exception as e:
            logger.error(f"Error incrementing OTP attempts: {e}")
            db.rollback()
    
    async def _send_email_otp(self, email: str, otp: str, purpose: str) -> bool:
        """Send OTP via email."""
        try:
            subject = "Your OTP Code"
            body = f"""
            <html>
            <body>
                <h2>Your OTP Code</h2>
                <p>Your OTP code is: <strong>{otp}</strong></p>
                <p>This code will expire in {self.otp_expiry_minutes} minutes.</p>
                <p>If you didn't request this code, please ignore this email.</p>
            </body>
            </html>
            """
            
            return self.email_service.send_simple_email(
                to_email=email,
                subject=subject,
                html_body=body
            )
        except Exception as e:
            logger.error(f"Error sending email OTP: {e}")
            return False
    
    async def _send_whatsapp_otp(self, phone: str, otp: str, purpose: str) -> bool:
        """Send OTP via WhatsApp."""
        try:
            message = f"Your OTP code is: {otp}. This code will expire in {self.otp_expiry_minutes} minutes."
            return await self.whatsapp_service.send_message(phone, message)
        except Exception as e:
            logger.error(f"Error sending WhatsApp OTP: {e}")
            return False
    
    async def cleanup_expired_otps(self) -> int:
        """Clean up expired OTP records."""
        try:
            # This would be implemented with actual database operations
            # For now, we'll use a placeholder
            return 0
        except Exception as e:
            logger.error(f"Error cleaning up expired OTPs: {e}")
            return 0

