"""
AWS service client configuration and base functionality.
"""
import boto3
from typing import Optional
from ..settings import settings
import logging

logger = logging.getLogger(__name__)


class AWSService:
    """Base AWS service class with common configuration."""
    
    def __init__(self):
        self.region = settings.aws_region
        self.access_key_id = settings.aws_access_key_id
        self.secret_access_key = settings.aws_secret_access_key
        
        # Initialize clients
        self._s3_client = None
        self._ses_client = None
        self._sns_client = None
        self._sqs_client = None
    
    @property
    def s3_client(self):
        """Get S3 client with lazy initialization."""
        if self._s3_client is None:
            self._s3_client = boto3.client(
                's3',
                region_name=self.region,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key
            )
        return self._s3_client
    
    @property
    def ses_client(self):
        """Get SES client with lazy initialization."""
        if self._ses_client is None:
            ses_region = settings.ses_region or self.region
            self._ses_client = boto3.client(
                'ses',
                region_name=ses_region,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key
            )
        return self._ses_client
    
    @property
    def sns_client(self):
        """Get SNS client with lazy initialization."""
        if self._sns_client is None:
            self._sns_client = boto3.client(
                'sns',
                region_name=self.region,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key
            )
        return self._sns_client
    
    @property
    def sqs_client(self):
        """Get SQS client with lazy initialization."""
        if self._sqs_client is None:
            self._sqs_client = boto3.client(
                'sqs',
                region_name=self.region,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key
            )
        return self._sqs_client
    
    def test_connection(self) -> dict:
        """Test AWS service connections."""
        results = {}
        
        try:
            # Test S3 connection
            self.s3_client.list_buckets()
            results['s3'] = 'connected'
        except Exception as e:
            logger.error(f"S3 connection failed: {e}")
            results['s3'] = f'error: {str(e)}'
        
        try:
            # Test SES connection
            self.ses_client.get_send_quota()
            results['ses'] = 'connected'
        except Exception as e:
            logger.error(f"SES connection failed: {e}")
            results['ses'] = f'error: {str(e)}'
        
        return results
