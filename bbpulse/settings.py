"""
Application settings and configuration management.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    database_url: str = "postgresql://postgres:root@localhost:5432/bbpulse"
    
    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    # S3 Configuration
    s3_bucket: str = "blubus-operator-docs"
    s3_upload_prefix: str = "operators"
    s3_signed_url_expiry: int = 900  # 15 minutes
    s3_download_url_expiry: int = 3600  # 1 hour
    
    # SES Configuration
    ses_region: Optional[str] = None
    ses_source_email: str = "noreply@blubus.com"
    ses_reply_to_email: Optional[str] = None
    
    # Celery Configuration
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    celery_task_always_eager: bool = True  # Set to True to disable Celery for development
    
    # JWT Configuration
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # OTP Configuration
    otp_expire_minutes: int = 5
    max_login_attempts: int = 5
    
    # WhatsApp Configuration
    WA_API_URL: str = "https://graph.facebook.com/v22.0"
    WA_API_TOKEN: str = "EAAQlp2DbAt4BO1BG2X7XqThmllRcqedFmoif6HrhBTprFkwidmwKHBILx9GuYWJZBUxuxZCC0mUggUSTM2LvhHD3brUX2c5fb9WtaXIbHNVuxSUKxDxyi1H1cQl7A697MCFGuse8jMN7ayGU48Yy16CtwhPwqUBZAvhco320Wl7WLXgvqjT8hqROZC79iSujuAZDZD"
    WA_PHONE_NUMBER_ID: str = "513292218537898" # for phone number +91 8296964424
    WA_BUSINESS_ACCOUNT_ID: str = "518136178052232" # for go2tax
    WA_SIGNATURE: str = "GO2TAX4321"
    GO2TAX_MOBILE: str = "8296964424"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # Application Configuration
    debug: bool = False
    log_level: str = "INFO"
    
    # Email Templates
    email_templates_bucket: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()

