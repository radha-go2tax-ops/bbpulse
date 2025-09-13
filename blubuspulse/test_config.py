"""
Test configuration for BluBus Plus.
"""
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .database import Base
from .settings import Settings

# Override settings for testing
class TestSettings(Settings):
    database_url: str = "sqlite:///./test_blubuspulse.db"
    aws_region: str = "us-east-1"
    aws_access_key_id: str = "test_key"
    aws_secret_access_key: str = "test_secret"
    s3_bucket: str = "test-bucket"
    s3_upload_prefix: str = "test-operators"
    ses_source_email: str = "test@blubus.com"
    jwt_secret_key: str = "test-secret-key-for-testing-only"
    debug: bool = True
    log_level: str = "DEBUG"

# Create test database engine
test_engine = create_engine(
    TestSettings().database_url,
    connect_args={"check_same_thread": False} if "sqlite" in TestSettings().database_url else {}
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def get_test_db():
    """Get test database session."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_test_tables():
    """Create test database tables."""
    Base.metadata.create_all(bind=test_engine)

def drop_test_tables():
    """Drop test database tables."""
    Base.metadata.drop_all(bind=test_engine)
