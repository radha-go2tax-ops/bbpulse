"""
Test cases for AWS services functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
from bbpulse.services.s3_service import S3DocumentService
from bbpulse.services.email_service import SESEmailService
from bbpulse.test_config import TestSettings

# Override settings for testing
import bbpulse.settings
bbpulse.settings.settings = TestSettings()

class TestS3Service:
    """Test S3 document service."""
    
    @patch('bbpulse.services.s3_service.boto3.client')
    def test_generate_presigned_post(self, mock_boto_client):
        """Test generating presigned POST URL."""
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        
        # Mock presigned POST response
        mock_s3.generate_presigned_post.return_value = {
            "url": "https://test-bucket.s3.amazonaws.com/",
            "fields": {"key": "test-file.pdf"}
        }
        
        s3_service = S3DocumentService()
        result = s3_service.generate_presigned_post(
            operator_id="1",
            filename="test.pdf",
            content_type="application/pdf",
            doc_type="RC"
        )
        
        assert "upload_url" in result
        assert "file_key" in result
        assert "fields" in result
        assert "expires_in" in result
        
        # Verify S3 client was called correctly
        mock_s3.generate_presigned_post.assert_called_once()
        call_args = mock_s3.generate_presigned_post.call_args
        assert call_args[1]["Bucket"] == "test-bucket"
        assert "operators/1/documents/" in call_args[1]["Key"]
    
    @patch('bbpulse.services.s3_service.boto3.client')
    def test_generate_presigned_url(self, mock_boto_client):
        """Test generating presigned download URL."""
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.generate_presigned_url.return_value = "https://test-bucket.s3.amazonaws.com/test.pdf?signature=abc123"
        
        s3_service = S3DocumentService()
        result = s3_service.generate_presigned_url("test-file.pdf")
        
        assert result == "https://test-bucket.s3.amazonaws.com/test.pdf?signature=abc123"
        mock_s3.generate_presigned_url.assert_called_once()
    
    @patch('bbpulse.services.s3_service.boto3.client')
    def test_delete_document(self, mock_boto_client):
        """Test deleting document from S3."""
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        
        s3_service = S3DocumentService()
        result = s3_service.delete_document("test-file.pdf")
        
        assert result is True
        mock_s3.delete_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test-file.pdf"
        )
    
    @patch('bbpulse.services.s3_service.boto3.client')
    def test_get_document_metadata(self, mock_boto_client):
        """Test getting document metadata."""
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        
        # Mock head_object response
        mock_s3.head_object.return_value = {
            "ContentType": "application/pdf",
            "ContentLength": 1024,
            "LastModified": "2024-01-01T00:00:00Z",
            "ETag": '"abc123"',
            "StorageClass": "STANDARD"
        }
        
        s3_service = S3DocumentService()
        result = s3_service.get_document_metadata("test-file.pdf")
        
        assert result["content_type"] == "application/pdf"
        assert result["content_length"] == 1024
        assert result["etag"] == '"abc123"'
    
    @patch('bbpulse.services.s3_service.boto3.client')
    def test_check_document_exists(self, mock_boto_client):
        """Test checking if document exists."""
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        
        # Test existing document
        s3_service = S3DocumentService()
        result = s3_service.check_document_exists("existing-file.pdf")
        assert result is True
        
        # Test non-existing document
        mock_s3.head_object.side_effect = mock_s3.exceptions.NoSuchKey()
        result = s3_service.check_document_exists("non-existing-file.pdf")
        assert result is False


class TestSESService:
    """Test SES email service."""
    
    @patch('bbpulse.services.email_service.boto3.client')
    def test_send_templated_email(self, mock_boto_client):
        """Test sending templated email."""
        mock_ses = MagicMock()
        mock_boto_client.return_value = mock_ses
        mock_ses.send_templated_email.return_value = {"MessageId": "test-message-id"}
        
        ses_service = SESEmailService()
        result = ses_service.send_templated_email(
            to_email="test@example.com",
            template_name="test_template",
            template_data={"name": "Test User"},
            operator_id=1
        )
        
        assert result == "test-message-id"
        mock_ses.send_templated_email.assert_called_once()
    
    @patch('bbpulse.services.email_service.boto3.client')
    def test_send_simple_email(self, mock_boto_client):
        """Test sending simple email."""
        mock_ses = MagicMock()
        mock_boto_client.return_value = mock_ses
        mock_ses.send_email.return_value = {"MessageId": "test-message-id"}
        
        ses_service = SESEmailService()
        result = ses_service.send_simple_email(
            to_email="test@example.com",
            subject="Test Subject",
            html_body="<p>Test HTML</p>",
            text_body="Test Text",
            operator_id=1
        )
        
        assert result == "test-message-id"
        mock_ses.send_email.assert_called_once()
    
    @patch('bbpulse.services.email_service.boto3.client')
    def test_create_email_template(self, mock_boto_client):
        """Test creating email template."""
        mock_ses = MagicMock()
        mock_boto_client.return_value = mock_ses
        
        ses_service = SESEmailService()
        result = ses_service.create_email_template(
            template_name="test_template",
            subject="Test Subject",
            html_template="<p>Test HTML</p>",
            text_template="Test Text"
        )
        
        assert result is True
        mock_ses.create_template.assert_called_once()
    
    @patch('bbpulse.services.email_service.boto3.client')
    def test_get_send_quota(self, mock_boto_client):
        """Test getting send quota."""
        mock_ses = MagicMock()
        mock_boto_client.return_value = mock_ses
        mock_ses.get_send_quota.return_value = {
            "Max24HourSend": 200.0,
            "MaxSendRate": 1.0,
            "SentLast24Hours": 0.0
        }
        
        ses_service = SESEmailService()
        result = ses_service.get_send_quota()
        
        assert result["Max24HourSend"] == 200.0
        assert result["MaxSendRate"] == 1.0
        assert result["SentLast24Hours"] == 0.0


class TestAWSServiceIntegration:
    """Test AWS service integration."""
    
    @patch('bbpulse.services.aws_service.boto3.client')
    def test_aws_connection_test(self, mock_boto_client):
        """Test AWS connection testing."""
        from bbpulse.services.aws_service import AWSService
        
        # Mock successful connections
        mock_s3 = MagicMock()
        mock_ses = MagicMock()
        mock_boto_client.side_effect = [mock_s3, mock_ses]
        
        aws_service = AWSService()
        result = aws_service.test_connection()
        
        assert "s3" in result
        assert "ses" in result
        assert result["s3"] == "connected"
        assert result["ses"] == "connected"
    
    @patch('bbpulse.services.aws_service.boto3.client')
    def test_aws_connection_failure(self, mock_boto_client):
        """Test AWS connection failure handling."""
        from bbpulse.services.aws_service import AWSService
        
        # Mock connection failures
        mock_boto_client.side_effect = Exception("Connection failed")
        
        aws_service = AWSService()
        result = aws_service.test_connection()
        
        assert "s3" in result
        assert "ses" in result
        assert "error" in result["s3"]
        assert "error" in result["ses"]


if __name__ == "__main__":
    pytest.main([__file__])

