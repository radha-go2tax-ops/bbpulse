"""
Token Service for managing JWT tokens and blacklisting.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models import TokenBlacklist, User
from ..auth.jwt_handler import JWTHandler
from ..settings import settings

logger = logging.getLogger(__name__)


class TokenService:
    """Service for managing JWT tokens."""
    
    def __init__(self):
        self.jwt_handler = JWTHandler()
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = settings.jwt_refresh_token_expire_days
    
    async def create_tokens(
        self, 
        user_id: str, 
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create access and refresh tokens.
        
        Args:
            user_id: User ID
            additional_claims: Additional claims to include in tokens
            
        Returns:
            Dictionary containing tokens and metadata
        """
        try:
            # Prepare claims
            claims = {
                "user_id": user_id,
                "token_type": "access"
            }
            if additional_claims:
                claims.update(additional_claims)
            
            # Create access token
            access_token = self.jwt_handler.create_access_token(
                user_id=user_id,
                additional_claims=claims,
                expires_delta=timedelta(minutes=self.access_token_expire_minutes)
            )
            
            # Create refresh token
            refresh_claims = {
                "user_id": user_id,
                "token_type": "refresh"
            }
            refresh_token = self.jwt_handler.create_refresh_token(
                user_id=user_id,
                additional_claims=refresh_claims,
                expires_delta=timedelta(days=self.refresh_token_expire_days)
            )
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": self.access_token_expire_minutes * 60
            }
            
        except Exception as e:
            logger.error(f"Error creating tokens: {e}")
            raise
    
    async def renew_tokens(self, refresh_token: str, db: Session) -> Optional[Dict[str, Any]]:
        """
        Renew tokens using refresh token.
        
        Args:
            refresh_token: Refresh token
            db: Database session
            
        Returns:
            Dictionary containing new tokens or None if invalid
        """
        try:
            # Verify refresh token
            payload = self.jwt_handler.verify_token(refresh_token, "refresh")
            if not payload:
                return None
            
            user_id = payload.get("sub")
            if not user_id:
                return None
            
            # Check if token is blacklisted
            if await self._is_token_blacklisted(refresh_token, db):
                return None
            
            # Check if this is an operator user (integer ID) or regular user (UUID)
            from ..models import OperatorUser
            import uuid
            
            # Try OperatorUser first (integer ID)
            try:
                operator_user = db.query(OperatorUser).filter(OperatorUser.id == int(user_id)).first()
                if operator_user and operator_user.is_active:
                    # Operator user found - use JWT handler directly
                    additional_claims = {
                        "operator_id": operator_user.operator_id
                    }
                    tokens = self.jwt_handler.create_token_pair(str(operator_user.id), additional_claims)
                    
                    # Convert to expected format
                    return {
                        "access_token": tokens["access_token"],
                        "refresh_token": tokens["refresh_token"],
                        "token_type": "bearer",
                        "expires_in": self.jwt_handler.access_token_expire_minutes * 60
                    }
            except (ValueError, TypeError):
                # user_id is not an integer, try as UUID for regular user
                pass
            
            # Try regular User table (UUID)
            try:
                user_uuid = uuid.UUID(user_id)
                user = db.query(User).filter(User.id == user_uuid).first()
                if user and user.is_active:
                    # Regular user found
                    additional_claims = {
                        "email": user.email,
                        "mobile": user.mobile,
                        "full_name": user.full_name
                    }
                    return await self.create_tokens(user_id, additional_claims)
            except (ValueError, TypeError):
                # user_id is not a valid UUID
                pass
            
            # No valid user found
            return None
            
        except Exception as e:
            logger.error(f"Error renewing tokens: {e}")
            return None
    
    async def blacklist_token(
        self, 
        token: str, 
        token_type: str, 
        user_id: str, 
        db: Session
    ) -> bool:
        """
        Add token to blacklist.
        
        Args:
            token: JWT token to blacklist
            token_type: Type of token (access or refresh)
            user_id: User ID
            db: Database session
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Decode token to get expiration
            payload = self.jwt_handler.verify_token(token, token_type)
            if not payload:
                return False
            
            expires_at = datetime.fromtimestamp(payload.get("exp", 0))
            
            # Create blacklist record
            blacklist_record = TokenBlacklist(
                token_id=token,
                user_id=user_id,
                token_type=token_type,
                expires_at=expires_at
            )
            
            db.add(blacklist_record)
            db.commit()
            
            logger.info(f"Token blacklisted for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error blacklisting token: {e}")
            return False
    
    async def verify_token(self, token: str, token_type: str, db: Session) -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token to verify
            token_type: Type of token (access or refresh)
            db: Database session
            
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            # Check if token is blacklisted
            if await self._is_token_blacklisted(token, db):
                return None
            
            # Verify token
            payload = self.jwt_handler.verify_token(token, token_type)
            if not payload:
                return None
            
            # Check if token is expired
            exp = payload.get("exp")
            if exp and datetime.utcnow().timestamp() > exp:
                return None
            
            return payload
            
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None
    
    async def _is_token_blacklisted(self, token: str, db: Session) -> bool:
        """Check if token is blacklisted."""
        try:
            blacklist_record = db.query(TokenBlacklist).filter(
                TokenBlacklist.token_id == token
            ).first()
            
            return blacklist_record is not None
            
        except Exception as e:
            logger.error(f"Error checking token blacklist: {e}")
            return False
    
    async def cleanup_expired_tokens(self, db: Session) -> int:
        """
        Clean up expired blacklisted tokens.
        
        Args:
            db: Database session
            
        Returns:
            Number of tokens cleaned up
        """
        try:
            current_time = datetime.utcnow()
            
            # Delete expired blacklisted tokens
            expired_tokens = db.query(TokenBlacklist).filter(
                TokenBlacklist.expires_at < current_time
            ).all()
            
            count = len(expired_tokens)
            for token in expired_tokens:
                db.delete(token)
            
            db.commit()
            
            if count > 0:
                logger.info(f"Cleaned up {count} expired blacklisted tokens")
            
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {e}")
            return 0

