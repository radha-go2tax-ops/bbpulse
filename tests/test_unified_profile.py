"""
Tests for unified profile endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from bbpulse.main import app
from bbpulse.models import OperatorUser, User, Operator
from bbpulse.database import get_db
from bbpulse.auth.jwt_handler import JWTHandler
import uuid
from datetime import datetime

client = TestClient(app)

# Mock database session
@pytest.fixture
def db_session():
    """Mock database session for testing."""
    # This would be replaced with actual test database setup
    pass

@pytest.fixture
def test_operator_and_user(db_session):
    """Create test operator and user for testing."""
    # This would create test data in the database
    # For now, we'll mock the data
    operator = Operator(
        id=1,
        company_name="Test Company",
        contact_email="test@company.com",
        status="ACTIVE"
    )
    
    operator_user = OperatorUser(
        id=1,
        operator_id=1,
        email="admin@testcompany.com",
        first_name="Test",
        last_name="Admin",
        role="ADMIN",
        is_active=True,
        email_verified=True,
        mobile_verified=True,
        created_at=datetime.utcnow()
    )
    
    general_user = User(
        id=uuid.uuid4(),
        email="user@example.com",
        full_name="John Doe",
        source="email",
        is_active=True,
        is_email_verified=True,
        is_mobile_verified=False,
        created_at=datetime.utcnow()
    )
    
    return operator, operator_user, general_user

@pytest.fixture
def jwt_handler():
    """JWT handler for creating test tokens."""
    return JWTHandler()

def test_get_unified_profile_operator_user(test_operator_and_user, jwt_handler):
    """Test getting unified profile for operator user."""
    operator, operator_user, general_user = test_operator_and_user
    
    # Create JWT token for operator user
    token_data = {
        "sub": str(operator_user.id),
        "email": operator_user.email,
        "role": operator_user.role
    }
    access_token = jwt_handler.create_access_token(token_data)
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test unified profile endpoint
    response = client.get("/auth/profile", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["user_type"] == "operator_user"
    assert data["data"]["email"] == "admin@testcompany.com"
    assert data["data"]["first_name"] == "Test"
    assert data["data"]["last_name"] == "Admin"
    assert data["data"]["role"] == "ADMIN"
    assert data["data"]["operator_id"] == 1

def test_get_unified_profile_general_user(test_operator_and_user, jwt_handler):
    """Test getting unified profile for general user."""
    operator, operator_user, general_user = test_operator_and_user
    
    # Create JWT token for general user
    token_data = {
        "sub": str(general_user.id),
        "email": general_user.email,
        "source": general_user.source
    }
    access_token = jwt_handler.create_access_token(token_data)
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test unified profile endpoint
    response = client.get("/auth/profile", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["user_type"] == "user"
    assert data["data"]["email"] == "user@example.com"
    assert data["data"]["full_name"] == "John Doe"
    assert data["data"]["source"] == "email"
    assert "role" not in data["data"]  # General users don't have role
    assert "operator_id" not in data["data"]  # General users don't have operator_id

def test_get_operator_profile_specific(test_operator_and_user, jwt_handler):
    """Test getting operator profile using specific endpoint."""
    operator, operator_user, general_user = test_operator_and_user
    
    # Create JWT token for operator user
    token_data = {
        "sub": str(operator_user.id),
        "email": operator_user.email,
        "role": operator_user.role
    }
    access_token = jwt_handler.create_access_token(token_data)
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test operator-specific profile endpoint
    response = client.get("/auth/operator-profile", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["user_type"] == "operator_user"
    assert data["data"]["email"] == "admin@testcompany.com"
    assert data["data"]["role"] == "ADMIN"

def test_get_user_profile_specific(test_operator_and_user, jwt_handler):
    """Test getting user profile using specific endpoint."""
    operator, operator_user, general_user = test_operator_and_user
    
    # Create JWT token for general user
    token_data = {
        "sub": str(general_user.id),
        "email": general_user.email,
        "source": general_user.source
    }
    access_token = jwt_handler.create_access_token(token_data)
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test user-specific profile endpoint
    response = client.get("/auth/user-profile", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["user_type"] == "user"
    assert data["data"]["email"] == "user@example.com"
    assert data["data"]["full_name"] == "John Doe"

def test_get_operator_profile_wrong_user_type(test_operator_and_user, jwt_handler):
    """Test getting operator profile with general user (should fail)."""
    operator, operator_user, general_user = test_operator_and_user
    
    # Create JWT token for general user
    token_data = {
        "sub": str(general_user.id),
        "email": general_user.email,
        "source": general_user.source
    }
    access_token = jwt_handler.create_access_token(token_data)
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test operator-specific profile endpoint with general user
    response = client.get("/auth/operator-profile", headers=headers)
    
    assert response.status_code == 400
    assert "general users only" in response.json()["detail"]

def test_get_user_profile_wrong_user_type(test_operator_and_user, jwt_handler):
    """Test getting user profile with operator user (should fail)."""
    operator, operator_user, general_user = test_operator_and_user
    
    # Create JWT token for operator user
    token_data = {
        "sub": str(operator_user.id),
        "email": operator_user.email,
        "role": operator_user.role
    }
    access_token = jwt_handler.create_access_token(token_data)
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test user-specific profile endpoint with operator user
    response = client.get("/auth/user-profile", headers=headers)
    
    assert response.status_code == 400
    assert "operator users only" in response.json()["detail"]

def test_update_unified_profile_operator_user(test_operator_and_user, jwt_handler):
    """Test updating unified profile for operator user."""
    operator, operator_user, general_user = test_operator_and_user
    
    # Create JWT token for operator user
    token_data = {
        "sub": str(operator_user.id),
        "email": operator_user.email,
        "role": operator_user.role
    }
    access_token = jwt_handler.create_access_token(token_data)
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Update profile data
    update_data = {
        "full_name": "Updated Name",
        "email": "updated@testcompany.com",
        "mobile": "+919876543210"
    }
    
    # Test unified profile update endpoint
    response = client.put("/auth/profile", json=update_data, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["user_type"] == "operator_user"
    assert data["data"]["first_name"] == "Updated Name"
    assert data["data"]["email"] == "updated@testcompany.com"
    assert data["data"]["mobile"] == "+919876543210"

def test_update_unified_profile_general_user(test_operator_and_user, jwt_handler):
    """Test updating unified profile for general user."""
    operator, operator_user, general_user = test_operator_and_user
    
    # Create JWT token for general user
    token_data = {
        "sub": str(general_user.id),
        "email": general_user.email,
        "source": general_user.source
    }
    access_token = jwt_handler.create_access_token(token_data)
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Update profile data
    update_data = {
        "full_name": "Updated User Name",
        "email": "updated@example.com",
        "mobile": "+919876543210"
    }
    
    # Test unified profile update endpoint
    response = client.put("/auth/profile", json=update_data, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["user_type"] == "user"
    assert data["data"]["full_name"] == "Updated User Name"
    assert data["data"]["email"] == "updated@example.com"
    assert data["data"]["mobile"] == "+919876543210"

def test_get_profile_unauthorized():
    """Test getting profile without authentication."""
    response = client.get("/auth/profile")
    assert response.status_code == 401

def test_update_profile_unauthorized():
    """Test updating profile without authentication."""
    update_data = {
        "full_name": "Test Name"
    }
    response = client.put("/auth/profile", json=update_data)
    assert response.status_code == 401
