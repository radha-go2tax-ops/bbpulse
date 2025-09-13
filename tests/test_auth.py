"""
Test cases for authentication functionality.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from bbpulse.main import app
from bbpulse.test_config import get_test_db, create_test_tables, drop_test_tables, TestSettings
from bbpulse.models import Operator, OperatorUser
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

def test_login_success(db_session: Session, test_operator_and_user):
    """Test successful login."""
    operator, user = test_operator_and_user
    
    response = client.post("/auth/login", json={
        "email": "admin@testcompany.com",
        "password": "testpassword123"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(db_session: Session, test_operator_and_user):
    """Test login with invalid credentials."""
    operator, user = test_operator_and_user
    
    # Wrong password
    response = client.post("/auth/login", json={
        "email": "admin@testcompany.com",
        "password": "wrongpassword"
    })
    
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]
    
    # Wrong email
    response = client.post("/auth/login", json={
        "email": "wrong@email.com",
        "password": "testpassword123"
    })
    
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]

def test_login_inactive_user(db_session: Session, test_operator_and_user):
    """Test login with inactive user."""
    operator, user = test_operator_and_user
    
    # Deactivate user
    user.is_active = False
    db_session.commit()
    
    response = client.post("/auth/login", json={
        "email": "admin@testcompany.com",
        "password": "testpassword123"
    })
    
    assert response.status_code == 403
    assert "deactivated" in response.json()["detail"]

def test_get_current_user_info(db_session: Session, test_operator_and_user):
    """Test getting current user information."""
    operator, user = test_operator_and_user
    
    # Login first
    login_response = client.post("/auth/login", json={
        "email": "admin@testcompany.com",
        "password": "testpassword123"
    })
    
    tokens = login_response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    
    # Get user info
    response = client.get("/auth/me", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@testcompany.com"
    assert data["first_name"] == "Test"
    assert data["last_name"] == "Admin"
    assert data["role"] == "ADMIN"

def test_get_current_user_unauthorized():
    """Test getting current user without authentication."""
    response = client.get("/auth/me")
    assert response.status_code == 401

def test_refresh_token(db_session: Session, test_operator_and_user):
    """Test token refresh."""
    operator, user = test_operator_and_user
    
    # Login first
    login_response = client.post("/auth/login", json={
        "email": "admin@testcompany.com",
        "password": "testpassword123"
    })
    
    tokens = login_response.json()
    refresh_token = tokens["refresh_token"]
    
    # Refresh token
    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

def test_refresh_token_invalid(db_session: Session, test_operator_and_user):
    """Test refresh with invalid token."""
    response = client.post("/auth/refresh", json={"refresh_token": "invalid_token"})
    assert response.status_code == 401

def test_change_password(db_session: Session, test_operator_and_user):
    """Test changing password."""
    operator, user = test_operator_and_user
    
    # Login first
    login_response = client.post("/auth/login", json={
        "email": "admin@testcompany.com",
        "password": "testpassword123"
    })
    
    tokens = login_response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    
    # Change password
    response = client.post("/auth/change-password", json={
        "current_password": "testpassword123",
        "new_password": "newpassword123"
    }, headers=headers)
    
    assert response.status_code == 200
    assert "changed successfully" in response.json()["message"]
    
    # Try to login with old password
    old_login_response = client.post("/auth/login", json={
        "email": "admin@testcompany.com",
        "password": "testpassword123"
    })
    assert old_login_response.status_code == 401
    
    # Login with new password
    new_login_response = client.post("/auth/login", json={
        "email": "admin@testcompany.com",
        "password": "newpassword123"
    })
    assert new_login_response.status_code == 200

def test_change_password_wrong_current(db_session: Session, test_operator_and_user):
    """Test changing password with wrong current password."""
    operator, user = test_operator_and_user
    
    # Login first
    login_response = client.post("/auth/login", json={
        "email": "admin@testcompany.com",
        "password": "testpassword123"
    })
    
    tokens = login_response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    
    # Try to change password with wrong current password
    response = client.post("/auth/change-password", json={
        "current_password": "wrongpassword",
        "new_password": "newpassword123"
    }, headers=headers)
    
    assert response.status_code == 400
    assert "incorrect" in response.json()["detail"]

@patch('bbpulse.tasks.email_tasks.send_password_reset_email.delay')
def test_forgot_password(mock_send_email, db_session: Session, test_operator_and_user):
    """Test forgot password functionality."""
    operator, user = test_operator_and_user
    mock_send_email.return_value = None
    
    response = client.post("/auth/forgot-password", json={
        "email": "admin@testcompany.com"
    })
    
    assert response.status_code == 200
    assert "reset link has been sent" in response.json()["message"]
    mock_send_email.assert_called_once()

def test_forgot_password_nonexistent_user():
    """Test forgot password with non-existent user."""
    response = client.post("/auth/forgot-password", json={
        "email": "nonexistent@email.com"
    })
    
    # Should still return success to avoid revealing user existence
    assert response.status_code == 200
    assert "reset link has been sent" in response.json()["message"]

def test_logout(db_session: Session, test_operator_and_user):
    """Test logout functionality."""
    operator, user = test_operator_and_user
    
    # Login first
    login_response = client.post("/auth/login", json={
        "email": "admin@testcompany.com",
        "password": "testpassword123"
    })
    
    tokens = login_response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    
    # Logout
    response = client.post("/auth/logout", headers=headers)
    
    assert response.status_code == 200
    assert "successfully" in response.json()["message"]

if __name__ == "__main__":
    pytest.main([__file__])

