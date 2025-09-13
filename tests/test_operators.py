"""
Test cases for operator management functionality.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from blubuspulse.main import app
from blubuspulse.test_config import get_test_db, create_test_tables, drop_test_tables, TestSettings
from blubuspulse.models import Operator, OperatorUser
from blubuspulse.auth.jwt_handler import JWTHandler

# Override settings for testing
import blubuspulse.settings
blubuspulse.settings.settings = TestSettings()

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
def test_operator_data():
    """Sample operator data for testing."""
    return {
        "company_name": "Test Bus Company",
        "contact_email": "test@testcompany.com",
        "contact_phone": "+1234567890",
        "business_license": "BL123456",
        "address": "123 Test Street",
        "city": "Test City",
        "state": "Test State",
        "country": "Test Country",
        "postal_code": "12345"
    }

@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "email": "admin@testcompany.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "Admin",
        "role": "ADMIN"
    }

@pytest.fixture
def jwt_handler():
    """JWT handler for testing."""
    return JWTHandler()

def test_create_operator(db_session: Session, test_operator_data):
    """Test creating a new operator."""
    response = client.post("/operators/", json=test_operator_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["company_name"] == test_operator_data["company_name"]
    assert data["contact_email"] == test_operator_data["contact_email"]
    assert data["status"] == "PENDING"
    assert "id" in data

def test_create_operator_duplicate_email(db_session: Session, test_operator_data):
    """Test creating operator with duplicate email."""
    # Create first operator
    client.post("/operators/", json=test_operator_data)
    
    # Try to create second operator with same email
    response = client.post("/operators/", json=test_operator_data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_get_operator_not_found():
    """Test getting non-existent operator."""
    response = client.get("/operators/999")
    assert response.status_code == 401  # Unauthorized without token

def test_list_operators_unauthorized():
    """Test listing operators without authentication."""
    response = client.get("/operators/")
    assert response.status_code == 401

def test_operator_workflow(db_session: Session, test_operator_data, test_user_data, jwt_handler):
    """Test complete operator workflow."""
    # 1. Create operator
    operator_response = client.post("/operators/", json=test_operator_data)
    assert operator_response.status_code == 201
    operator_id = operator_response.json()["id"]
    
    # 2. Create admin user for operator
    user_data = {**test_user_data, "operator_id": operator_id}
    user_response = client.post(f"/operators/{operator_id}/users", json=user_data)
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # 3. Login as user
    login_response = client.post("/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    
    # 4. Get operator details (authenticated)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    operator_details = client.get(f"/operators/{operator_id}", headers=headers)
    assert operator_details.status_code == 200
    assert operator_details.json()["id"] == operator_id
    
    # 5. Update operator
    update_data = {"company_name": "Updated Test Company"}
    update_response = client.put(f"/operators/{operator_id}", json=update_data, headers=headers)
    assert update_response.status_code == 200
    assert update_response.json()["company_name"] == "Updated Test Company"

def test_operator_activation_workflow(db_session: Session, test_operator_data, test_user_data, jwt_handler):
    """Test operator activation workflow."""
    # Create operator and user
    operator_response = client.post("/operators/", json=test_operator_data)
    operator_id = operator_response.json()["id"]
    
    user_data = {**test_user_data, "operator_id": operator_id}
    user_response = client.post(f"/operators/{operator_id}/users", json=user_data)
    user_id = user_response.json()["id"]
    
    # Login as admin (simulate admin user)
    login_response = client.post("/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    tokens = login_response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    
    # Activate operator
    activate_response = client.post(f"/operators/{operator_id}/activate", headers=headers)
    assert activate_response.status_code == 200
    assert activate_response.json()["status"] == "ACTIVE"
    
    # Suspend operator
    suspend_response = client.post(f"/operators/{operator_id}/suspend", 
                                 json={"reason": "Test suspension"}, headers=headers)
    assert suspend_response.status_code == 200
    assert suspend_response.json()["status"] == "SUSPENDED"

if __name__ == "__main__":
    pytest.main([__file__])
