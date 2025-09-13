import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from blubuspulse.main import app
from blubuspulse.database import get_db, Base
from blubuspulse import models

# Create in-memory test database for faster tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create tables once for all tests
Base.metadata.create_all(bind=engine)

client = TestClient(app)

# Add a fixture to clean up data between tests
@pytest.fixture(autouse=True)
def clean_database():
    """Clean up database after each test."""
    yield
    # Clean up all tables after each test
    for table in reversed(Base.metadata.sorted_tables):
        engine.execute(table.delete())


def test_root_endpoint():
    """Test the root endpoint returns correct message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Welcome to BluBus Pulse Backend API"
    assert response.json()["version"] == "1.0.0"


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "blubuspulse"


def test_get_bus_stops():
    """Test getting all bus stops."""
    response = client.get("/bus-stops")
    assert response.status_code == 200
    bus_stops = response.json()
    assert isinstance(bus_stops, list)
    assert all("id" in stop for stop in bus_stops)
    assert all("name" in stop for stop in bus_stops)


def test_create_bus_stop():
    """Test creating a new bus stop."""
    bus_stop_data = {
        "name": "Test Stop",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "description": "Test bus stop",
        "address": "123 Test St"
    }
    response = client.post("/bus-stops", json=bus_stop_data)
    assert response.status_code == 200
    stop = response.json()
    assert stop["name"] == "Test Stop"
    assert stop["latitude"] == 40.7128


def test_get_bus_stop_by_id():
    """Test getting a specific bus stop by ID."""
    # First create a bus stop
    bus_stop_data = {
        "name": "Test Stop",
        "latitude": 40.7128,
        "longitude": -74.0060
    }
    create_response = client.post("/bus-stops", json=bus_stop_data)
    stop_id = create_response.json()["id"]
    
    # Then get it
    response = client.get(f"/bus-stops/{stop_id}")
    assert response.status_code == 200
    stop = response.json()
    assert stop["id"] == stop_id
    assert stop["name"] == "Test Stop"


def test_get_bus_stop_not_found():
    """Test getting a non-existent bus stop."""
    response = client.get("/bus-stops/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Bus stop not found"


def test_get_routes():
    """Test getting all routes."""
    response = client.get("/routes")
    assert response.status_code == 200
    routes = response.json()
    assert isinstance(routes, list)
    assert all("id" in route for route in routes)
    assert all("name" in route for route in routes)


def test_create_route():
    """Test creating a new route."""
    # First create some bus stops
    stop1_data = {"name": "Stop 1", "latitude": 40.7128, "longitude": -74.0060}
    stop2_data = {"name": "Stop 2", "latitude": 40.7589, "longitude": -73.9851}
    
    stop1_response = client.post("/bus-stops", json=stop1_data)
    stop2_response = client.post("/bus-stops", json=stop2_data)
    
    stop1_id = stop1_response.json()["id"]
    stop2_id = stop2_response.json()["id"]
    
    route_data = {
        "name": "Test Route",
        "description": "Test route description",
        "estimated_duration": 30,
        "stop_ids": [stop1_id, stop2_id]
    }
    response = client.post("/routes", json=route_data)
    assert response.status_code == 200
    route = response.json()
    assert route["name"] == "Test Route"
    assert len(route["stops"]) == 2


def test_get_buses():
    """Test getting all buses."""
    response = client.get("/buses")
    assert response.status_code == 200
    buses = response.json()
    assert isinstance(buses, list)
    assert all("id" in bus for bus in buses)
    assert all("route_id" in bus for bus in buses)


def test_create_bus():
    """Test creating a new bus."""
    # First create a route
    stop_data = {"name": "Test Stop", "latitude": 40.7128, "longitude": -74.0060}
    stop_response = client.post("/bus-stops", json=stop_data)
    stop_id = stop_response.json()["id"]
    
    route_data = {
        "name": "Test Route",
        "stop_ids": [stop_id]
    }
    route_response = client.post("/routes", json=route_data)
    route_id = route_response.json()["id"]
    
    bus_data = {
        "bus_number": "TEST001",
        "route_id": route_id,
        "current_stop_id": stop_id,
        "capacity": 50
    }
    response = client.post("/buses", json=bus_data)
    assert response.status_code == 200
    bus = response.json()
    assert bus["bus_number"] == "TEST001"
    assert bus["route_id"] == route_id


def test_track_bus_not_found():
    """Test tracking a non-existent bus."""
    response = client.get("/tracking/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Bus not found"
