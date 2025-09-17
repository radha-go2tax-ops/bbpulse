"""
Authentication API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from ..database import get_db
from ..models import OperatorUser
from ..schemas import (
    UserResponse
)
from ..auth.dependencies import get_current_user, get_current_operator_user
from ..auth.jwt_handler import JWTHandler
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
jwt_handler = JWTHandler()










@router.post("/logout")
async def logout(
    current_user: OperatorUser = Depends(get_current_operator_user)
):
    """Logout user (client should discard tokens)."""
    # In a stateless JWT system, logout is handled client-side
    # You could implement token blacklisting here if needed
    logger.info(f"User {current_user.id} logged out")
    return {"message": "Logged out successfully"}



