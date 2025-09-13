"""
Rate Limiting Service for controlling request rates.
"""
import logging
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models import User
from ..settings import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Service for rate limiting requests."""
    
    def __init__(self):
        self.redis_url = getattr(settings, 'redis_url', 'redis://localhost:6379/0')
        self.rate_limits = {
            'login_attempts': {'max_attempts': 5, 'window_minutes': 15},
            'otp_requests': {'max_attempts': 3, 'window_minutes': 5},
            'registration_attempts': {'max_attempts': 3, 'window_minutes': 10},
            'password_reset': {'max_attempts': 3, 'window_minutes': 10}
        }
    
    async def check_rate_limit(
        self, 
        identifier: str, 
        action: str, 
        db: Session
    ) -> tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Check if request is within rate limits.
        
        Args:
            identifier: Unique identifier (IP, user_id, email, etc.)
            action: Action being performed (login, otp_request, etc.)
            db: Database session
            
        Returns:
            Tuple of (is_allowed, message, rate_limit_info)
        """
        try:
            if action not in self.rate_limits:
                return True, "Rate limit not configured", None
            
            limit_config = self.rate_limits[action]
            max_attempts = limit_config['max_attempts']
            window_minutes = limit_config['window_minutes']
            
            # For now, we'll use a simple in-memory approach
            # In production, you'd use Redis for distributed rate limiting
            current_time = datetime.utcnow()
            window_start = current_time - timedelta(minutes=window_minutes)
            
            # Check rate limit based on action
            if action == 'login_attempts':
                return await self._check_login_rate_limit(identifier, max_attempts, window_start, db)
            elif action == 'otp_requests':
                return await self._check_otp_rate_limit(identifier, max_attempts, window_start, db)
            elif action == 'registration_attempts':
                return await self._check_registration_rate_limit(identifier, max_attempts, window_start, db)
            elif action == 'password_reset':
                return await self._check_password_reset_rate_limit(identifier, max_attempts, window_start, db)
            else:
                return True, "Action allowed", None
                
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True, "Rate limit check failed", None
    
    async def _check_login_rate_limit(
        self, 
        identifier: str, 
        max_attempts: int, 
        window_start: datetime, 
        db: Session
    ) -> tuple[bool, str, Optional[Dict[str, Any]]]:
        """Check login rate limit."""
        try:
            # Get user by identifier (email or mobile)
            user = None
            if '@' in identifier:
                user = db.query(User).filter(User.email == identifier).first()
            else:
                user = db.query(User).filter(User.mobile == identifier).first()
            
            if not user:
                return True, "User not found", None
            
            # Check if user is locked due to too many attempts
            if user.login_attempts >= max_attempts:
                # Check if lockout period has expired
                if user.last_login and user.last_login < window_start:
                    # Reset login attempts
                    user.login_attempts = 0
                    db.commit()
                    return True, "Rate limit reset", None
                else:
                    remaining_time = self._calculate_remaining_time(user.last_login, window_start)
                    return False, f"Account locked. Try again in {remaining_time} minutes", {
                        'locked': True,
                        'remaining_time': remaining_time
                    }
            
            return True, "Login allowed", None
            
        except Exception as e:
            logger.error(f"Login rate limit check error: {e}")
            return True, "Rate limit check failed", None
    
    async def _check_otp_rate_limit(
        self, 
        identifier: str, 
        max_attempts: int, 
        window_start: datetime, 
        db: Session
    ) -> tuple[bool, str, Optional[Dict[str, Any]]]:
        """Check OTP request rate limit."""
        try:
            # In a real implementation, you'd store OTP request timestamps in Redis
            # For now, we'll use a simplified approach
            
            # Check if identifier has made too many OTP requests
            # This would typically be stored in Redis with TTL
            otp_requests = await self._get_otp_requests_count(identifier, window_start)
            
            if otp_requests >= max_attempts:
                remaining_time = self._calculate_remaining_time(window_start, datetime.utcnow())
                return False, f"Too many OTP requests. Try again in {remaining_time} minutes", {
                    'remaining_time': remaining_time,
                    'max_attempts': max_attempts
                }
            
            # Record this OTP request
            await self._record_otp_request(identifier)
            
            return True, "OTP request allowed", None
            
        except Exception as e:
            logger.error(f"OTP rate limit check error: {e}")
            return True, "Rate limit check failed", None
    
    async def _check_registration_rate_limit(
        self, 
        identifier: str, 
        max_attempts: int, 
        window_start: datetime, 
        db: Session
    ) -> tuple[bool, str, Optional[Dict[str, Any]]]:
        """Check registration rate limit."""
        try:
            # Check if identifier has made too many registration attempts
            registration_attempts = await self._get_registration_attempts_count(identifier, window_start)
            
            if registration_attempts >= max_attempts:
                remaining_time = self._calculate_remaining_time(window_start, datetime.utcnow())
                return False, f"Too many registration attempts. Try again in {remaining_time} minutes", {
                    'remaining_time': remaining_time,
                    'max_attempts': max_attempts
                }
            
            # Record this registration attempt
            await self._record_registration_attempt(identifier)
            
            return True, "Registration allowed", None
            
        except Exception as e:
            logger.error(f"Registration rate limit check error: {e}")
            return True, "Rate limit check failed", None
    
    async def _check_password_reset_rate_limit(
        self, 
        identifier: str, 
        max_attempts: int, 
        window_start: datetime, 
        db: Session
    ) -> tuple[bool, str, Optional[Dict[str, Any]]]:
        """Check password reset rate limit."""
        try:
            # Check if identifier has made too many password reset requests
            reset_attempts = await self._get_password_reset_attempts_count(identifier, window_start)
            
            if reset_attempts >= max_attempts:
                remaining_time = self._calculate_remaining_time(window_start, datetime.utcnow())
                return False, f"Too many password reset requests. Try again in {remaining_time} minutes", {
                    'remaining_time': remaining_time,
                    'max_attempts': max_attempts
                }
            
            # Record this password reset attempt
            await self._record_password_reset_attempt(identifier)
            
            return True, "Password reset allowed", None
            
        except Exception as e:
            logger.error(f"Password reset rate limit check error: {e}")
            return True, "Rate limit check failed", None
    
    def _calculate_remaining_time(self, start_time: datetime, current_time: datetime) -> int:
        """Calculate remaining time in minutes."""
        if not start_time:
            return 0
        
        elapsed = current_time - start_time
        remaining_seconds = max(0, 900 - elapsed.total_seconds())  # 15 minutes window
        return int(remaining_seconds / 60)
    
    async def _get_otp_requests_count(self, identifier: str, window_start: datetime) -> int:
        """Get OTP requests count for identifier."""
        # In a real implementation, this would query Redis
        # For now, return 0 to allow requests
        return 0
    
    async def _record_otp_request(self, identifier: str) -> None:
        """Record OTP request for identifier."""
        # In a real implementation, this would store in Redis with TTL
        pass
    
    async def _get_registration_attempts_count(self, identifier: str, window_start: datetime) -> int:
        """Get registration attempts count for identifier."""
        # In a real implementation, this would query Redis
        # For now, return 0 to allow requests
        return 0
    
    async def _record_registration_attempt(self, identifier: str) -> None:
        """Record registration attempt for identifier."""
        # In a real implementation, this would store in Redis with TTL
        pass
    
    async def _get_password_reset_attempts_count(self, identifier: str, window_start: datetime) -> int:
        """Get password reset attempts count for identifier."""
        # In a real implementation, this would query Redis
        # For now, return 0 to allow requests
        return 0
    
    async def _record_password_reset_attempt(self, identifier: str) -> None:
        """Record password reset attempt for identifier."""
        # In a real implementation, this would store in Redis with TTL
        pass
    
    async def reset_rate_limit(self, identifier: str, action: str) -> bool:
        """
        Reset rate limit for identifier and action.
        
        Args:
            identifier: Unique identifier
            action: Action to reset
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # In a real implementation, this would clear Redis keys
            logger.info(f"Rate limit reset for {identifier} - {action}")
            return True
        except Exception as e:
            logger.error(f"Rate limit reset error: {e}")
            return False

