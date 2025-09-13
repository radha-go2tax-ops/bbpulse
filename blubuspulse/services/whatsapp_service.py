"""
WhatsApp Service for sending messages via WhatsApp API.
"""
import logging
import httpx
from typing import Optional
from ..settings import settings

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service for sending WhatsApp messages."""
    
    def __init__(self):
        self.api_url = getattr(settings, 'WA_API_URL', 'https://api.whatsapp.com')
        self.api_token = getattr(settings, 'WA_API_TOKEN', '')
        self.timeout = 30
    
    async def send_message(self, phone_number: str, message: str) -> bool:
        """
        Send a WhatsApp message.
        
        Args:
            phone_number: Recipient's phone number (with country code)
            message: Message content
            
        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            # Format phone number (remove any non-digit characters except +)
            formatted_phone = self._format_phone_number(phone_number)
            
            # Prepare request data
            data = {
                "to": formatted_phone,
                "text": message,
                "type": "text"
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            # Send request
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/messages",
                    json=data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    logger.info(f"WhatsApp message sent successfully to {formatted_phone}")
                    return True
                else:
                    logger.error(f"WhatsApp API error: {response.status_code} - {response.text}")
                    return False
                    
        except httpx.TimeoutException:
            logger.error(f"WhatsApp API timeout for {phone_number}")
            return False
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return False
    
    async def send_otp_message(self, phone_number: str, otp: str, purpose: str = "verification") -> bool:
        """
        Send OTP message via WhatsApp.
        
        Args:
            phone_number: Recipient's phone number
            otp: OTP code
            purpose: Purpose of OTP
            
        Returns:
            True if message sent successfully, False otherwise
        """
        message = f"Your OTP code is: {otp}. This code will expire in 5 minutes. Do not share this code with anyone."
        return await self.send_message(phone_number, message)
    
    def _format_phone_number(self, phone_number: str) -> str:
        """
        Format phone number for WhatsApp API.
        
        Args:
            phone_number: Raw phone number
            
        Returns:
            Formatted phone number
        """
        # Remove all non-digit characters except +
        cleaned = ''.join(c for c in phone_number if c.isdigit() or c == '+')
        
        # Ensure it starts with country code
        if not cleaned.startswith('+'):
            # Assume it's a US number if no country code
            cleaned = '+1' + cleaned
        
        return cleaned
    
    async def verify_phone_number(self, phone_number: str) -> bool:
        """
        Verify if a phone number is valid for WhatsApp.
        
        Args:
            phone_number: Phone number to verify
            
        Returns:
            True if valid, False otherwise
        """
        try:
            formatted_phone = self._format_phone_number(phone_number)
            
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_url}/phone_numbers/{formatted_phone}",
                    headers=headers
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Error verifying phone number: {e}")
            return False
