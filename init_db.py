#!/usr/bin/env python3
"""
Database initialization script for BluBus Pulse backend.
This script creates the database tables and populates them with sample data.
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from blubuspulse.database import DATABASE_URL, Base, engine
from blubuspulse import models, crud, schemas

def create_database():
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

def populate_sample_data():
    """Populate the database with sample data."""
    print("Populating database with sample data...")
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Create sample bus stops
        bus_stops_data = [
            schemas.BusStopCreate(
                name="Central Station",
                latitude=40.7128,
                longitude=-74.0060,
                description="Main transportation hub",
                address="123 Main St, City Center"
            ),
            schemas.BusStopCreate(
                name="University Campus",
                latitude=40.7589,
                longitude=-73.9851,
                description="University main entrance",
                address="456 University Ave, Campus"
            ),
            schemas.BusStopCreate(
                name="Shopping Mall",
                latitude=40.7505,
                longitude=-73.9934,
                description="Large shopping center",
                address="789 Commerce Blvd, Shopping District"
            ),
            schemas.BusStopCreate(
                name="Airport Terminal",
                latitude=40.6892,
                longitude=-74.1745,
                description="International airport terminal",
                address="321 Airport Rd, Airport"
            ),
            schemas.BusStopCreate(
                name="Hospital",
                latitude=40.7614,
                longitude=-73.9776,
                description="City General Hospital",
                address="654 Health St, Medical District"
            )
        ]
        
        created_stops = []
        for stop_data in bus_stops_data:
            stop = crud.create_bus_stop(db, stop_data)
            created_stops.append(stop)
            print(f"Created bus stop: {stop.name}")
        
        # Create sample routes
        routes_data = [
            schemas.RouteCreate(
                name="Route A - City Center Loop",
                description="Circular route through city center",
                estimated_duration=30,
                stop_ids=[1, 2, 3, 1]  # Central -> University -> Mall -> Central
            ),
            schemas.RouteCreate(
                name="Route B - Airport Express",
                description="Direct route to airport",
                estimated_duration=45,
                stop_ids=[1, 4]  # Central -> Airport
            ),
            schemas.RouteCreate(
                name="Route C - Medical District",
                description="Route serving medical facilities",
                estimated_duration=25,
                stop_ids=[2, 5, 3]  # University -> Hospital -> Mall
            )
        ]
        
        created_routes = []
        for route_data in routes_data:
            route = crud.create_route(db, route_data)
            created_routes.append(route)
            print(f"Created route: {route.name}")
        
        # Create sample buses
        buses_data = [
            schemas.BusCreate(
                bus_number="A001",
                route_id=1,
                current_stop_id=1,
                next_stop_id=2,
                estimated_arrival=5,
                status="in_transit",
                capacity=50,
                current_passengers=25
            ),
            schemas.BusCreate(
                bus_number="A002",
                route_id=1,
                current_stop_id=3,
                next_stop_id=1,
                estimated_arrival=8,
                status="at_stop",
                capacity=50,
                current_passengers=40
            ),
            schemas.BusCreate(
                bus_number="B001",
                route_id=2,
                current_stop_id=1,
                next_stop_id=4,
                estimated_arrival=15,
                status="in_transit",
                capacity=60,
                current_passengers=35
            ),
            schemas.BusCreate(
                bus_number="C001",
                route_id=3,
                current_stop_id=2,
                next_stop_id=5,
                estimated_arrival=3,
                status="in_transit",
                capacity=45,
                current_passengers=20
            )
        ]
        
        for bus_data in buses_data:
            bus = crud.create_bus(db, bus_data)
            print(f"Created bus: {bus.bus_number}")
        
        # Create some sample location data
        location_data = [
            schemas.BusLocationCreate(
                bus_id=1,
                latitude=40.7130,
                longitude=-74.0055,
                speed=25.5,
                direction=45.0
            ),
            schemas.BusLocationCreate(
                bus_id=2,
                latitude=40.7500,
                longitude=-73.9930,
                speed=0.0,
                direction=0.0
            ),
            schemas.BusLocationCreate(
                bus_id=3,
                latitude=40.7120,
                longitude=-74.0100,
                speed=30.2,
                direction=180.0
            )
        ]
        
        for location in location_data:
            crud.create_bus_location(db, location)
        
        print("Sample data populated successfully!")
        
    except Exception as e:
        print(f"Error populating sample data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def main():
    """Main function to initialize the database."""
    print("Initializing BluBus Pulse backend database...")
    print(f"Database URL: {DATABASE_URL}")
    
    try:
        # Create tables
        create_database()
        
        # Populate with sample data
        populate_sample_data()
        
        print("\nDatabase initialization completed successfully!")
        print("You can now start the application with: uv run python run.py")
        
    except Exception as e:
        print(f"Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
