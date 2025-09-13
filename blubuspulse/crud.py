"""
Database CRUD operations for BluBus Pulse backend.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Optional
from . import models, schemas


# Bus Stop CRUD operations
def get_bus_stop(db: Session, stop_id: int) -> Optional[models.BusStop]:
    """Get a bus stop by ID."""
    return db.query(models.BusStop).filter(models.BusStop.id == stop_id).first()


def get_bus_stops(db: Session, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[models.BusStop]:
    """Get all bus stops with pagination."""
    query = db.query(models.BusStop)
    if active_only:
        query = query.filter(models.BusStop.is_active == 1)
    return query.offset(skip).limit(limit).all()


def create_bus_stop(db: Session, stop: schemas.BusStopCreate) -> models.BusStop:
    """Create a new bus stop."""
    db_stop = models.BusStop(**stop.dict())
    db.add(db_stop)
    db.commit()
    db.refresh(db_stop)
    return db_stop


def update_bus_stop(db: Session, stop_id: int, stop: schemas.BusStopUpdate) -> Optional[models.BusStop]:
    """Update a bus stop."""
    db_stop = get_bus_stop(db, stop_id)
    if db_stop:
        update_data = stop.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_stop, field, value)
        db.commit()
        db.refresh(db_stop)
    return db_stop


def delete_bus_stop(db: Session, stop_id: int) -> bool:
    """Soft delete a bus stop (set is_active to 0)."""
    db_stop = get_bus_stop(db, stop_id)
    if db_stop:
        db_stop.is_active = 0
        db.commit()
        return True
    return False


# Route CRUD operations
def get_route(db: Session, route_id: int) -> Optional[models.Route]:
    """Get a route by ID."""
    return db.query(models.Route).filter(models.Route.id == route_id).first()


def get_routes(db: Session, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[models.Route]:
    """Get all routes with pagination."""
    query = db.query(models.Route)
    if active_only:
        query = query.filter(models.Route.is_active == 1)
    return query.offset(skip).limit(limit).all()


def create_route(db: Session, route: schemas.RouteCreate) -> models.Route:
    """Create a new route."""
    db_route = models.Route(
        name=route.name,
        description=route.description,
        estimated_duration=route.estimated_duration
    )
    db.add(db_route)
    db.flush()  # Flush to get the ID
    
    # Add stops to the route
    for stop_id in route.stop_ids:
        stop = get_bus_stop(db, stop_id)
        if stop:
            db_route.stops.append(stop)
    
    db.commit()
    db.refresh(db_route)
    return db_route


def update_route(db: Session, route_id: int, route: schemas.RouteUpdate) -> Optional[models.Route]:
    """Update a route."""
    db_route = get_route(db, route_id)
    if db_route:
        update_data = route.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_route, field, value)
        db.commit()
        db.refresh(db_route)
    return db_route


def delete_route(db: Session, route_id: int) -> bool:
    """Soft delete a route."""
    db_route = get_route(db, route_id)
    if db_route:
        db_route.is_active = 0
        db.commit()
        return True
    return False


# Bus CRUD operations
def get_bus(db: Session, bus_id: int) -> Optional[models.Bus]:
    """Get a bus by ID."""
    return db.query(models.Bus).filter(models.Bus.id == bus_id).first()


def get_buses(db: Session, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[models.Bus]:
    """Get all buses with pagination."""
    query = db.query(models.Bus)
    if active_only:
        query = query.filter(models.Bus.is_active == 1)
    return query.offset(skip).limit(limit).all()


def get_buses_by_route(db: Session, route_id: int, active_only: bool = True) -> List[models.Bus]:
    """Get buses by route ID."""
    query = db.query(models.Bus).filter(models.Bus.route_id == route_id)
    if active_only:
        query = query.filter(models.Bus.is_active == 1)
    return query.all()


def create_bus(db: Session, bus: schemas.BusCreate) -> models.Bus:
    """Create a new bus."""
    db_bus = models.Bus(**bus.dict())
    db.add(db_bus)
    db.commit()
    db.refresh(db_bus)
    return db_bus


def update_bus(db: Session, bus_id: int, bus: schemas.BusUpdate) -> Optional[models.Bus]:
    """Update a bus."""
    db_bus = get_bus(db, bus_id)
    if db_bus:
        update_data = bus.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_bus, field, value)
        db.commit()
        db.refresh(db_bus)
    return db_bus


def delete_bus(db: Session, bus_id: int) -> bool:
    """Soft delete a bus."""
    db_bus = get_bus(db, bus_id)
    if db_bus:
        db_bus.is_active = 0
        db.commit()
        return True
    return False


# Bus Location CRUD operations
def create_bus_location(db: Session, location: schemas.BusLocationCreate) -> models.BusLocation:
    """Create a new bus location record."""
    db_location = models.BusLocation(**location.dict())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location


def get_bus_locations(db: Session, bus_id: int, limit: int = 10) -> List[models.BusLocation]:
    """Get recent locations for a bus."""
    return (
        db.query(models.BusLocation)
        .filter(models.BusLocation.bus_id == bus_id)
        .order_by(desc(models.BusLocation.recorded_at))
        .limit(limit)
        .all()
    )


def get_latest_bus_location(db: Session, bus_id: int) -> Optional[models.BusLocation]:
    """Get the latest location for a bus."""
    return (
        db.query(models.BusLocation)
        .filter(models.BusLocation.bus_id == bus_id)
        .order_by(desc(models.BusLocation.recorded_at))
        .first()
    )
