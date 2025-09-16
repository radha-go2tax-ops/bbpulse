#!/usr/bin/env python3
"""
PostgreSQL setup script for BluBus Pulse.
This script will:
1. Check if PostgreSQL is installed and running
2. Create the database if it doesn't exist
3. Install required Python packages
4. Run database migrations
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from bbpulse.settings import settings

def check_postgresql_installation():
    """Check if PostgreSQL is installed and running."""
    print("🔍 Checking PostgreSQL installation...")
    
    try:
        # Try to connect to PostgreSQL
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT version()"))
        print("✅ PostgreSQL is running and accessible")
        return True
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {str(e)}")
        return False

def install_postgresql_packages():
    """Install required Python packages for PostgreSQL."""
    print("\n📦 Installing PostgreSQL packages...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "psycopg2-binary"
        ], check=True, capture_output=True, text=True)
        print("✅ psycopg2-binary installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install psycopg2-binary: {e.stderr}")
        return False

def create_database():
    """Create the database if it doesn't exist."""
    print("\n🗄️  Creating database...")
    
    # Extract database info from URL
    db_url = settings.database_url
    # Format: postgresql://user:password@host:port/database
    parts = db_url.replace("postgresql://", "").split("/")
    db_name = parts[1]
    connection_info = parts[0].split("@")
    user_pass = connection_info[0].split(":")
    host_port = connection_info[1].split(":")
    
    user = user_pass[0]
    password = user_pass[1]
    host = host_port[0]
    port = host_port[1] if len(host_port) > 1 else "5432"
    
    # Connect to postgres database to create our database
    admin_url = f"postgresql://{user}:{password}@{host}:{port}/postgres"
    
    try:
        admin_engine = create_engine(admin_url)
        with admin_engine.connect() as conn:
            # Check if database exists
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
            if result.fetchone():
                print(f"✅ Database '{db_name}' already exists")
            else:
                # Create database
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                conn.commit()
                print(f"✅ Database '{db_name}' created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create database: {str(e)}")
        return False

def run_migrations():
    """Run database migrations."""
    print("\n🔄 Running database migrations...")
    
    try:
        from bbpulse.database import create_tables
        create_tables()
        print("✅ Database tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create tables: {str(e)}")
        return False

def print_setup_instructions():
    """Print instructions for manual PostgreSQL setup."""
    print("\n📋 Manual PostgreSQL Setup Instructions:")
    print("=" * 50)
    
    system = platform.system().lower()
    
    if system == "windows":
        print("1. Download PostgreSQL from: https://www.postgresql.org/download/windows/")
        print("2. Install PostgreSQL with default settings")
        print("3. Start PostgreSQL service")
        print("4. Set password for 'postgres' user to 'password'")
        print("5. Run this script again")
    elif system == "darwin":  # macOS
        print("1. Install PostgreSQL using Homebrew:")
        print("   brew install postgresql")
        print("2. Start PostgreSQL service:")
        print("   brew services start postgresql")
        print("3. Create user and database:")
        print("   createuser -s postgres")
        print("   createdb bbpulse")
        print("4. Set password for postgres user:")
        print("   psql -U postgres -c \"ALTER USER postgres PASSWORD 'password';\"")
        print("5. Run this script again")
    else:  # Linux
        print("1. Install PostgreSQL:")
        print("   sudo apt-get update")
        print("   sudo apt-get install postgresql postgresql-contrib")
        print("2. Start PostgreSQL service:")
        print("   sudo systemctl start postgresql")
        print("   sudo systemctl enable postgresql")
        print("3. Switch to postgres user and create database:")
        print("   sudo -u postgres psql")
        print("   CREATE USER postgres WITH PASSWORD 'password';")
        print("   CREATE DATABASE bbpulse OWNER postgres;")
        print("   GRANT ALL PRIVILEGES ON DATABASE bbpulse TO postgres;")
        print("   \\q")
        print("4. Run this script again")
    
    print("\n🐳 Alternative: Use Docker")
    print("   docker run --name postgres-bbpulse -e POSTGRES_PASSWORD=password -e POSTGRES_DB=bbpulse -p 5432:5432 -d postgres:15-alpine")

def main():
    """Main setup function."""
    print("🚀 PostgreSQL Setup for BluBus Pulse")
    print("=" * 40)
    
    # Check if PostgreSQL is accessible
    if check_postgresql_installation():
        # Install packages
        if not install_postgresql_packages():
            return False
        
        # Create database
        if not create_database():
            return False
        
        # Run migrations
        if not run_migrations():
            return False
        
        print("\n🎉 PostgreSQL setup completed successfully!")
        print("💡 You can now run your application with PostgreSQL")
        return True
    else:
        print("\n❌ PostgreSQL is not accessible")
        print_setup_instructions()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)



