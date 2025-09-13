# PostgreSQL Migration Summary

This document summarizes the changes made to migrate from SQLite to PostgreSQL and consolidate database configuration.

## Changes Made

### 1. Database Configuration Consolidation

**Files Modified:**
- `bbpulse/settings.py` - Updated default database URL to PostgreSQL
- `bbpulse/database.py` - Removed hardcoded defaults, now uses settings configuration

**Key Changes:**
- Single source of truth for database configuration in `settings.py`
- Removed duplicate database URL definitions
- Consistent use of Pydantic settings throughout the application

### 2. Dependencies Updated

**File Modified:**
- `pyproject.toml`

**Changes:**
- Replaced `pymysql>=1.1.2` with `psycopg2-binary>=2.9.9`
- Added PostgreSQL-specific database connector

### 3. Environment Configuration

**Files Modified:**
- `env.example` - Already had PostgreSQL configuration
- `env.test` - Updated to use PostgreSQL for testing

**Changes:**
- Consistent PostgreSQL URLs across all environments
- Test database uses port 5433 to avoid conflicts

### 4. Docker Configuration

**Files Created/Modified:**
- `docker-compose.yml` - New main development environment
- `docker-compose.test.yml` - Updated to use PostgreSQL instead of MySQL

**Services Included:**
- PostgreSQL 15 Alpine
- Redis 7 Alpine
- FastAPI application
- Celery worker

### 5. Migration Scripts

**Files Created:**
- `migrate_to_postgresql.py` - Migrates existing SQLite data to PostgreSQL
- `setup_postgresql.py` - Automated PostgreSQL setup and configuration

**Features:**
- Automated database creation
- Data migration with verification
- Cross-platform setup instructions
- Error handling and rollback capabilities

### 6. Documentation Updates

**File Modified:**
- `README.md`

**Updates:**
- Updated tech stack to reflect PostgreSQL
- Added multiple PostgreSQL setup options (Docker, Manual, Automated)
- Added Docker Compose usage instructions
- Updated prerequisites and installation steps

## Migration Steps

### For New Installations

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Set up PostgreSQL:**
   ```bash
   # Option 1: Docker (Recommended)
   docker run --name postgres-bbpulse -e POSTGRES_PASSWORD=password -e POSTGRES_DB=bbpulse -p 5432:5432 -d postgres:15-alpine
   
   # Option 2: Automated setup
   uv run python setup_postgresql.py
   ```

3. **Initialize database:**
   ```bash
   uv run python init_db.py
   ```

### For Existing SQLite Users

1. **Backup your data:**
   ```bash
   cp bbpulse.db bbpulse.db.backup
   ```

2. **Set up PostgreSQL:**
   ```bash
   uv run python setup_postgresql.py
   ```

3. **Migrate data:**
   ```bash
   uv run python migrate_to_postgresql.py
   ```

4. **Verify migration:**
   The migration script will automatically verify data integrity.

## Configuration Details

### Database URLs

- **Development:** `postgresql://postgres:password@localhost:5432/bbpulse`
- **Testing:** `postgresql://postgres:testpassword@localhost:5433/test_bbpulse`
- **Production:** Set via `DATABASE_URL` environment variable

### Environment Variables

The following environment variables control database behavior:

- `DATABASE_URL` - Full PostgreSQL connection string
- `DEBUG` - Controls SQL query logging (from settings.debug)

## Benefits of PostgreSQL

1. **Better Concurrency:** Handles multiple simultaneous connections
2. **Advanced Features:** Full-text search, JSON support, advanced indexing
3. **Production Ready:** Industry standard for production applications
4. **Scalability:** Better performance under load
5. **Data Integrity:** Robust ACID compliance and transaction handling

## Rollback Plan

If you need to rollback to SQLite:

1. **Revert settings.py:**
   ```python
   database_url: str = "sqlite:///./bbpulse.db"
   ```

2. **Revert database.py:**
   ```python
   DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bbpulse.db")
   ```

3. **Update pyproject.toml:**
   Remove `psycopg2-binary` and add back `pymysql`

4. **Restore SQLite database:**
   ```bash
   cp bbpulse.db.backup bbpulse.db
   ```

## Testing

Run the test suite to ensure everything works:

```bash
# Run all tests
uv run pytest

# Run with Docker Compose
docker-compose -f docker-compose.test.yml up --build
```

## Support

If you encounter issues:

1. Check PostgreSQL is running: `docker ps` or `systemctl status postgresql`
2. Verify connection: `uv run python -c "from bbpulse.database import engine; print(engine.execute('SELECT 1').scalar())"`
3. Check logs: `docker-compose logs postgres` or PostgreSQL logs
4. Run migration verification: `uv run python migrate_to_postgresql.py`


