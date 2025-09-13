# BluBus Pulse

A FastAPI-based backend service for the BluBus application, providing real-time bus tracking and route management capabilities. BluBus Pulse serves as the core API backend that powers the BluBus frontend application.

## About BluBus Pulse

BluBus Pulse is the backend API service that powers the **BluBus** application ecosystem. It provides all the core functionality needed for a modern bus tracking and public transportation system.

### Architecture
- **BluBus**: The main frontend application (mobile/web) that users interact with
- **BluBus Pulse**: This backend API service that provides data and functionality to BluBus
- **PostgreSQL Database**: Persistent storage for all bus, route, and location data

## Features

- 🚌 **Bus Stop Management**: Get information about bus stops and their locations
- 🛣️ **Route Management**: Manage bus routes and their associated stops
- 🚍 **Real-time Tracking**: Track buses and get estimated arrival times
- 📍 **Location Services**: GPS coordinates for bus stops
- 🔄 **RESTful API**: Clean and well-documented API endpoints
- 🧪 **Testing**: Comprehensive test suite with pytest
- 📚 **Auto Documentation**: Interactive API docs with Swagger UI

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and Object-Relational Mapping (ORM) library
- **PostgreSQL**: Primary database for data persistence
- **psycopg2**: PostgreSQL database connector for Python
- **Alembic**: Database migration tool
- **Pydantic**: Data validation using Python type annotations
- **Uvicorn**: ASGI server for running the application
- **uv**: Fast Python package manager and project manager
- **pytest**: Testing framework

## Prerequisites

- Python 3.13+
- uv package manager
- PostgreSQL 15+ (or use Docker)

## Installation

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source $HOME/.local/bin/env
   ```

2. **Clone and navigate to the project**:
   ```bash
   cd bbpulse
   ```

3. **Install dependencies**:
   ```bash
   uv sync
   ```

4. **Set up PostgreSQL database**:
   
   **Option A: Using Docker (Recommended)**
   ```bash
   # Start PostgreSQL with Docker
   docker run --name postgres-bbpulse -e POSTGRES_PASSWORD=password -e POSTGRES_DB=bbpulse -p 5432:5432 -d postgres:15-alpine
   ```
   
   **Option B: Manual Installation**
   ```bash
   # Install PostgreSQL (Ubuntu/Debian)
   sudo apt-get update
   sudo apt-get install postgresql postgresql-contrib
   
   # Create database and user
   sudo -u postgres psql
   CREATE USER postgres WITH PASSWORD 'password';
   CREATE DATABASE bbpulse OWNER postgres;
   GRANT ALL PRIVILEGES ON DATABASE bbpulse TO postgres;
   \q
   ```
   
   **Option C: Automated Setup**
   ```bash
   # Copy environment configuration
   cp env.example .env
   
   # Run automated PostgreSQL setup
   uv run python setup_postgresql.py
   ```

5. **Initialize the database**:
   ```bash
   uv run python init_db.py
   ```

## Running the Application

### Development Mode

```bash
# Run the server using the run script
uv run python run.py
```

Or using uvicorn directly:
#  uv run uvicorn main:app --host 0.0.0.0 --port 8000
```bash
uv run uvicorn bbpulse.main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Production Mode

```bash
uv run uvicorn bbpulse.main:app --host 0.0.0.0 --port 8000
```

### Using Docker Compose (Recommended)

For a complete development environment with PostgreSQL and Redis:

```bash
# Start all services (PostgreSQL, Redis, App, Celery)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

This will start:
- PostgreSQL database on port 5432
- Redis on port 6379
- FastAPI application on port 8000
- Celery worker for background tasks

## API Endpoints

### Core Endpoints

- `GET /` - Welcome message and API information
- `GET /health` - Health check endpoint

### Bus Stops

- `GET /bus-stops` - Get all bus stops (with pagination)
- `GET /bus-stops/{stop_id}` - Get specific bus stop by ID
- `POST /bus-stops` - Create a new bus stop
- `PUT /bus-stops/{stop_id}` - Update a bus stop
- `DELETE /bus-stops/{stop_id}` - Delete a bus stop

### Routes

- `GET /routes` - Get all routes (with pagination)
- `GET /routes/{route_id}` - Get specific route by ID
- `POST /routes` - Create a new route
- `PUT /routes/{route_id}` - Update a route
- `DELETE /routes/{route_id}` - Delete a route

### Buses

- `GET /buses` - Get all buses (with pagination)
- `GET /buses/{bus_id}` - Get specific bus by ID
- `GET /buses/route/{route_id}` - Get buses by route ID
- `POST /buses` - Create a new bus
- `PUT /buses/{bus_id}` - Update a bus
- `DELETE /buses/{bus_id}` - Delete a bus

### Tracking

- `GET /tracking/{bus_id}` - Track specific bus location and status
- `POST /tracking/{bus_id}/location` - Update bus location
- `GET /tracking/{bus_id}/history` - Get bus location history

## Testing

Run the test suite:

```bash
# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run tests with coverage
uv run pytest --cov=main
```

## Development

### Code Formatting

```bash
# Format code with black
uv run black .

# Sort imports with isort
uv run isort .
```

### Adding Dependencies

```bash
# Add a new dependency
uv add package-name

# Add a development dependency
uv add --dev package-name
```

## Project Structure

```
bbpulse/
├── bbpulse/           # Main package directory
│   ├── __init__.py       # Package initialization
│   ├── main.py           # Main FastAPI application
│   ├── database.py       # Database configuration and connection
│   ├── models.py         # SQLAlchemy database models
│   ├── schemas.py        # Pydantic schemas for API validation
│   └── crud.py           # Database CRUD operations
├── run.py                # Simple script to run the application
├── init_db.py            # Database initialization script
├── pyproject.toml        # Project configuration and dependencies
├── pytest.ini           # Pytest configuration
├── env.example           # Environment variables template
├── README.md             # This file
├── tests/                # Test files
│   └── test_main.py     # Main test suite
└── .venv/                # Virtual environment (created by uv)
```

## Data Models

### BusStop
- `id`: Unique identifier
- `name`: Stop name
- `latitude`: GPS latitude
- `longitude`: GPS longitude
- `routes`: List of route names

### Route
- `id`: Unique identifier
- `name`: Route name
- `stops`: List of stop IDs
- `estimated_time`: Estimated travel time in minutes

### Bus
- `id`: Unique identifier
- `route_id`: Associated route ID
- `current_stop`: Current stop ID
- `next_stop`: Next stop ID
- `estimated_arrival`: Estimated arrival time in minutes

## Environment Variables

Copy `env.example` to `.env` and configure:

```bash
cp env.example .env
```

Available configuration options:
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `DEBUG`: Debug mode (default: True)

## Future Enhancements

- [ ] Database integration (SQLAlchemy + PostgreSQL)
- [ ] Real-time GPS tracking with WebSockets
- [ ] User authentication and authorization
- [ ] Push notifications for bus arrivals
- [ ] Route optimization algorithms
- [ ] Mobile app integration
- [ ] Analytics and reporting
- [ ] Docker containerization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License.

