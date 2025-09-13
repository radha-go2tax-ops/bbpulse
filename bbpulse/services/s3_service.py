"""
S3 document management service.
"""
import boto3
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import logging
from .aws_service import AWSService
from ..settings import settings

logger = logging.getLogger(__name__)


class S3DocumentService(AWSService):
    """Service for managing documents in S3."""
    
    def __init__(self):
        super().__init__()
        self.bucket = settings.s3_bucket
        self.upload_prefix = settings.s3_upload_prefix
        self.signed_url_expiry = settings.s3_signed_url_expiry
        self.download_url_expiry = settings.s3_download_url_expiry
    
    def generate_presigned_post(self, operator_id: str, filename: str, 
                               content_type: str, doc_type: str) -> Dict[str, Any]:
        """
        Generate presigned POST for direct S3 upload.
        
        Args:
            operator_id: ID of the operator
            filename: Original filename
            content_type: MIME type of the file
            doc_type: Type of document (RC, PERMIT, etc.)
            
        Returns:
            Dictionary containing presigned POST data and file key
        """
        try:
            # Generate unique file key
            file_extension = filename.split('.')[-1] if '.' in filename else ''
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_key = f"{self.upload_prefix}/{operator_id}/documents/{unique_filename}"
            
            # Set up conditions for the presigned POST
            conditions = [
                {"content-type": content_type},
                ["starts-with", "$key", f"{self.upload_prefix}/{operator_id}/documents/"],
                ["content-length-range", 1, 50 * 1024 * 1024]  # 50MB max
            ]
            
            # Generate presigned POST
            presigned_post = self.s3_client.generate_presigned_post(
                Bucket=self.bucket,
                Key=file_key,
                Fields={
                    "Content-Type": content_type,
                    "x-amz-meta-doc-type": doc_type,
                    "x-amz-meta-operator-id": operator_id,
                    "x-amz-meta-uploaded-at": datetime.utcnow().isoformat()
                },
                Conditions=conditions,
                ExpiresIn=self.signed_url_expiry
            )
            
            return {
                "upload_url": presigned_post["url"],
                "file_key": file_key,
                "fields": presigned_post["fields"],
                "expires_in": self.signed_url_expiry
            }
            
        except Exception as e:
            logger.error(f"Failed to generate presigned POST: {e}")
            raise
    
    def generate_presigned_url(self, file_key: str, expiry: Optional[int] = None) -> str:
        """
        Generate presigned URL for document download.
        
        Args:
            file_key: S3 object key
            expiry: URL expiry time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL for downloading the file
        """
        try:
            expiry = expiry or self.download_url_expiry
            
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': file_key},
                ExpiresIn=expiry
            )
            
            return presigned_url
            
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
    
    def delete_document(self, file_key: str) -> bool:
        """
        Delete document from S3.
        
        Args:
            file_key: S3 object key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=file_key)
            logger.info(f"Successfully deleted document: {file_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {file_key}: {e}")
            return False
    
    def get_document_metadata(self, file_key: str) -> Dict[str, Any]:
        """
        Get document metadata from S3.
        
        Args:
            file_key: S3 object key
            
        Returns:
            Dictionary containing document metadata
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket, Key=file_key)
            
            return {
                "content_type": response.get("ContentType"),
                "content_length": response.get("ContentLength"),
                "last_modified": response.get("LastModified"),
                "etag": response.get("ETag"),
                "metadata": response.get("Metadata", {}),
                "storage_class": response.get("StorageClass")
            }
            
        except Exception as e:
            logger.error(f"Failed to get document metadata for {file_key}: {e}")
            raise
    
    def copy_document(self, source_key: str, dest_key: str) -> bool:
        """
        Copy document within S3.
        
        Args:
            source_key: Source S3 object key
            dest_key: Destination S3 object key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            copy_source = {'Bucket': self.bucket, 'Key': source_key}
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket,
                Key=dest_key
            )
            logger.info(f"Successfully copied document from {source_key} to {dest_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to copy document from {source_key} to {dest_key}: {e}")
            return False
    
    def list_operator_documents(self, operator_id: str) -> list:
        """
        List all documents for an operator.
        
        Args:
            operator_id: ID of the operator
            
        Returns:
            List of document objects
        """
        try:
            prefix = f"{self.upload_prefix}/{operator_id}/documents/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix
            )
            
            documents = []
            for obj in response.get('Contents', []):
                documents.append({
                    "key": obj['Key'],
                    "size": obj['Size'],
                    "last_modified": obj['LastModified'],
                    "etag": obj['ETag']
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to list documents for operator {operator_id}: {e}")
            raise
    
    def check_document_exists(self, file_key: str) -> bool:
        """
        Check if a document exists in S3.
        
        Args:
            file_key: S3 object key
            
        Returns:
            True if document exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=file_key)
            return True
        except self.s3_client.exceptions.NoSuchKey:
            return False
        except Exception as e:
            logger.error(f"Error checking document existence for {file_key}: {e}")
            return False

