"""
Health check API routes.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from ..database import get_db
from ..schemas import HealthCheck, AWSHealthCheck
from ..services.aws_service import AWSService
from ..settings import settings
import redis
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])
aws_service = AWSService()


@router.get("/", response_model=HealthCheck)
async def health_check():
    """Basic health check endpoint."""
    return HealthCheck(
        status="healthy",
        service="bbpulse",
        timestamp=datetime.utcnow(),
        version=settings.version if hasattr(settings, 'version') else "1.0.0"
    )


@router.get("", response_model=HealthCheck)
async def health_check_root():
    """Root health check endpoint (no trailing slash)."""
    return HealthCheck(
        status="healthy",
        service="bbpulse",
        timestamp=datetime.utcnow(),
        version=settings.version if hasattr(settings, 'version') else "1.0.0"
    )


@router.get("/ready", response_model=HealthCheck)
async def readiness_check(db: Session = Depends(get_db)):
    """Kubernetes readiness probe."""
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        
        return HealthCheck(
            status="ready",
            service="bbpulse",
            timestamp=datetime.utcnow(),
            version=settings.version if hasattr(settings, 'version') else "1.0.0"
        )
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return HealthCheck(
            status="not_ready",
            service="bbpulse",
            timestamp=datetime.utcnow(),
            version=settings.version if hasattr(settings, 'version') else "1.0.0"
        )


@router.get("/live", response_model=HealthCheck)
async def liveness_check():
    """Kubernetes liveness probe."""
    return HealthCheck(
        status="alive",
        service="bbpulse",
        timestamp=datetime.utcnow(),
        version=settings.version if hasattr(settings, 'version') else "1.0.0"
    )


@router.get("/aws", response_model=AWSHealthCheck)
async def aws_health_check():
    """Check AWS services connectivity."""
    try:
        # Test AWS connections
        aws_status = aws_service.test_connection()
        
        # Test Redis connection
        try:
            redis_client = redis.from_url(settings.celery_broker_url)
            redis_client.ping()
            redis_status = "connected"
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            redis_status = f"error: {str(e)}"
        
        return AWSHealthCheck(
            status="healthy" if all(status == "connected" for status in aws_status.values()) else "degraded",
            service="bbpulse",
            timestamp=datetime.utcnow(),
            s3_status=aws_status.get("s3", "unknown"),
            ses_status=aws_status.get("ses", "unknown"),
            redis_status=redis_status
        )
        
    except Exception as e:
        logger.error(f"AWS health check failed: {e}")
        return AWSHealthCheck(
            status="unhealthy",
            service="bbpulse",
            timestamp=datetime.utcnow(),
            s3_status="error",
            ses_status="error",
            redis_status="error"
        )


@router.get("/database")
async def database_health_check(db: Session = Depends(get_db)):
    """Check database connectivity and performance."""
    try:
        # Test basic query
        result = db.execute(text("SELECT 1 as test")).fetchone()
        
        # Test table existence (PostgreSQL specific)
        tables = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
        table_count = len(tables)
        
        return {
            "status": "healthy",
            "database": "connected",
            "table_count": table_count,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }


@router.get("/otp-test")
async def otp_test_endpoint(db: Session = Depends(get_db)):
    """Test endpoint to get OTP from database for testing purposes."""
    try:
        from ..models import OTPRecord
        
        # Get the most recent OTP record
        otp_record = db.query(OTPRecord).filter(
            OTPRecord.is_used == False
        ).order_by(OTPRecord.created_at.desc()).first()
        
        if otp_record:
            return {
                "otp": otp_record.otp_code,
                "contact": otp_record.contact,
                "contact_type": otp_record.contact_type,
                "purpose": otp_record.purpose,
                "expires_at": otp_record.expires_at,
                "created_at": otp_record.created_at
            }
        else:
            return {
                "message": "No unused OTP found",
                "otp": None
            }
            
    except Exception as e:
        logger.error(f"OTP test endpoint failed: {e}")
        return {
            "error": str(e),
            "otp": None
        }

