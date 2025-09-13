"""
Test cases for document management functionality.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
from bbpulse.main import app
from bbpulse.test_config import get_test_db, create_test_tables, drop_test_tables, TestSettings
from bbpulse.models import Operator, OperatorUser, OperatorDocument
from bbpulse.auth.jwt_handler import JWTHandler

# Override settings for testing
import bbpulse.settings
bbpulse.settings.settings = TestSettings()

client = TestClient(app)

# Override database dependency
app.dependency_overrides[get_test_db] = get_test_db

@pytest.fixture(scope="function")
def db_session():
    """Create test database session."""
    create_test_tables()
    db = next(get_test_db())
    yield db
    db.close()
    drop_test_tables()

@pytest.fixture
def test_operator_and_user(db_session: Session):
    """Create test operator and user."""
    # Create operator
    operator = Operator(
        company_name="Test Bus Company",
        contact_email="test@testcompany.com",
        contact_phone="+1234567890",
        business_license="BL123456"
    )
    db_session.add(operator)
    db_session.commit()
    db_session.refresh(operator)
    
    # Create user
    jwt_handler = JWTHandler()
    user = OperatorUser(
        operator_id=operator.id,
        email="admin@testcompany.com",
        password_hash=jwt_handler.get_password_hash("testpassword123"),
        first_name="Test",
        last_name="Admin",
        role="ADMIN"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return operator, user

@pytest.fixture
def auth_headers(test_operator_and_user):
    """Get authentication headers."""
    operator, user = test_operator_and_user
    
    # Login to get token
    login_response = client.post("/auth/login", json={
        "email": "admin@testcompany.com",
        "password": "testpassword123"
    })
    
    tokens = login_response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}

@patch('bbpulse.services.s3_service.S3DocumentService.generate_presigned_post')
def test_generate_upload_url(mock_presigned_post, db_session, test_operator_and_user, auth_headers):
    """Test generating presigned upload URL."""
    operator, user = test_operator_and_user
    
    # Mock S3 response
    mock_presigned_post.return_value = {
        "upload_url": "https://test-bucket.s3.amazonaws.com/",
        "file_key": "operators/1/documents/test-file.pdf",
        "fields": {"key": "test-file.pdf"},
        "expires_in": 900
    }
    
    upload_request = {
        "filename": "test-document.pdf",
        "content_type": "application/pdf",
        "doc_type": "RC",
        "expiry_days": 365
    }
    
    response = client.post(
        f"/documents/operators/{operator.id}/upload-url",
        json=upload_request,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "upload_url" in data
    assert "file_key" in data
    assert data["file_key"] == "operators/1/documents/test-file.pdf"

@patch('bbpulse.services.s3_service.S3DocumentService.check_document_exists')
@patch('bbpulse.services.s3_service.S3DocumentService.get_document_metadata')
@patch('bbpulse.tasks.document_processing.process_document_upload.delay')
def test_register_document(mock_process_task, mock_metadata, mock_exists, 
                          db_session, test_operator_and_user, auth_headers):
    """Test registering uploaded document."""
    operator, user = test_operator_and_user
    
    # Mock S3 responses
    mock_exists.return_value = True
    mock_metadata.return_value = {
        "content_length": 1024,
        "content_type": "application/pdf"
    }
    mock_process_task.return_value = MagicMock()
    
    register_request = {
        "file_key": "operators/1/documents/test-file.pdf",
        "doc_type": "RC",
        "expiry_date": "2025-12-31T23:59:59Z",
        "uploaded_by": "admin@testcompany.com"
    }
    
    response = client.post(
        f"/documents/operators/{operator.id}/register",
        json=register_request,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["operator_id"] == operator.id
    assert data["doc_type"] == "RC"
    assert data["status"] == "UPLOADED"
    assert data["file_key"] == "operators/1/documents/test-file.pdf"

def test_register_document_not_found_in_s3(db_session, test_operator_and_user, auth_headers):
    """Test registering document that doesn't exist in S3."""
    operator, user = test_operator_and_user
    
    with patch('bbpulse.services.s3_service.S3DocumentService.check_document_exists') as mock_exists:
        mock_exists.return_value = False
        
        register_request = {
            "file_key": "operators/1/documents/nonexistent.pdf",
            "doc_type": "RC"
        }
        
        response = client.post(
            f"/documents/operators/{operator.id}/register",
            json=register_request,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "not found in S3" in response.json()["detail"]

def test_list_operator_documents(db_session, test_operator_and_user, auth_headers):
    """Test listing operator documents."""
    operator, user = test_operator_and_user
    
    # Create test documents
    doc1 = OperatorDocument(
        operator_id=operator.id,
        doc_type="RC",
        file_key="operators/1/documents/doc1.pdf",
        file_name="doc1.pdf",
        status="UPLOADED"
    )
    doc2 = OperatorDocument(
        operator_id=operator.id,
        doc_type="PERMIT",
        file_key="operators/1/documents/doc2.pdf",
        file_name="doc2.pdf",
        status="VERIFIED"
    )
    
    db_session.add_all([doc1, doc2])
    db_session.commit()
    
    # List all documents
    response = client.get(
        f"/documents/operators/{operator.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["doc_type"] in ["RC", "PERMIT"]
    assert data[1]["doc_type"] in ["RC", "PERMIT"]

def test_list_documents_filter_by_type(db_session, test_operator_and_user, auth_headers):
    """Test listing documents filtered by type."""
    operator, user = test_operator_and_user
    
    # Create test documents
    doc1 = OperatorDocument(
        operator_id=operator.id,
        doc_type="RC",
        file_key="operators/1/documents/doc1.pdf",
        file_name="doc1.pdf",
        status="UPLOADED"
    )
    doc2 = OperatorDocument(
        operator_id=operator.id,
        doc_type="PERMIT",
        file_key="operators/1/documents/doc2.pdf",
        file_name="doc2.pdf",
        status="VERIFIED"
    )
    
    db_session.add_all([doc1, doc2])
    db_session.commit()
    
    # Filter by doc_type
    response = client.get(
        f"/documents/operators/{operator.id}?doc_type=RC",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["doc_type"] == "RC"

@patch('bbpulse.services.s3_service.S3DocumentService.generate_presigned_url')
def test_get_download_url(mock_presigned_url, db_session, test_operator_and_user, auth_headers):
    """Test getting document download URL."""
    operator, user = test_operator_and_user
    
    # Create test document
    doc = OperatorDocument(
        operator_id=operator.id,
        doc_type="RC",
        file_key="operators/1/documents/test.pdf",
        file_name="test.pdf",
        status="VERIFIED"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    
    # Mock S3 response
    mock_presigned_url.return_value = "https://test-bucket.s3.amazonaws.com/test.pdf?signature=abc123"
    
    response = client.get(
        f"/documents/{doc.id}/download",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "download_url" in data
    assert "expires_in" in data
    assert data["file_name"] == "test.pdf"

def test_get_required_documents(db_session, test_operator_and_user, auth_headers):
    """Test getting required documents list."""
    operator, user = test_operator_and_user
    
    response = client.get(
        f"/documents/operators/{operator.id}/required",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    
    # Check required document types
    doc_types = [doc["type"] for doc in data]
    assert "RC" in doc_types
    assert "PERMIT" in doc_types
    assert "INSURANCE" in doc_types
    assert "TAX_CERTIFICATE" in doc_types

def test_document_access_control(db_session, test_operator_and_user):
    """Test document access control."""
    operator, user = test_operator_and_user
    
    # Create another operator
    other_operator = Operator(
        company_name="Other Company",
        contact_email="other@company.com"
    )
    db_session.add(other_operator)
    db_session.commit()
    db_session.refresh(other_operator)
    
    # Try to access other operator's documents
    response = client.get(f"/documents/operators/{other_operator.id}")
    assert response.status_code == 401  # Unauthorized

if __name__ == "__main__":
    pytest.main([__file__])

