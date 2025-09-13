"""
Basic tests for BluBus Pulse backend API without complex database operations.
These tests run faster and focus on core functionality.
"""
import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bbpulse.main import app
from bbpulse.database import get_db, Base

# Override database URL for testing to use SQLite
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Create test database
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create tables
Base.metadata.create_all(bind=engine)

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns correct message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Welcome to BluBus Pulse - Backend API for BluBus"
    assert response.json()["version"] == "1.0.0"


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "bbpulse"


def test_get_bus_stops_empty():
    """Test getting bus stops when database is empty."""
    response = client.get("/bus-stops")
    assert response.status_code == 200
    assert response.json() == []


def test_get_routes_empty():
    """Test getting routes when database is empty."""
    response = client.get("/routes")
    assert response.status_code == 200
    assert response.json() == []


def test_get_buses_empty():
    """Test getting buses when database is empty."""
    response = client.get("/buses")
    assert response.status_code == 200
    assert response.json() == []


def test_get_bus_stop_not_found():
    """Test getting a non-existent bus stop."""
    response = client.get("/bus-stops/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Bus stop not found"


def test_get_route_not_found():
    """Test getting a non-existent route."""
    response = client.get("/routes/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Route not found"


def test_get_bus_not_found():
    """Test getting a non-existent bus."""
    response = client.get("/buses/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Bus not found"


def test_track_bus_not_found():
    """Test tracking a non-existent bus."""
    response = client.get("/tracking/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Bus not found"

