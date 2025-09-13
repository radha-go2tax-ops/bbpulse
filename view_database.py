#!/usr/bin/env python3
"""
Script to view database tables and data for BluBus Pulse
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add the bbpulse module to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'bbpulse'))

from bbpulse.database import get_db, engine
from bbpulse.models import Base

def view_database_info():
    """View database information and tables"""
    print("=" * 60)
    print("BLUBUS PULSE DATABASE INFORMATION")
    print("=" * 60)
    
    # Get database URL
    load_dotenv()
    database_url = os.getenv("DATABASE_URL", "sqlite:///./bbpulse.db")
    print(f"Database URL: {database_url}")
    print()
    
    # Create engine
    engine = create_engine(database_url, echo=False)
    
    # Get inspector
    inspector = inspect(engine)
    
    # List all tables
    tables = inspector.get_table_names()
    print(f"Total Tables: {len(tables)}")
    print("Tables:")
    for i, table in enumerate(tables, 1):
        print(f"  {i}. {table}")
    print()
    
    # Show table details
    for table_name in tables:
        print(f"{'=' * 40}")
        print(f"TABLE: {table_name}")
        print(f"{'=' * 40}")
        
        # Get columns
        columns = inspector.get_columns(table_name)
        print("Columns:")
        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            default = f" DEFAULT {col['default']}" if col['default'] is not None else ""
            print(f"  - {col['name']}: {col['type']} {nullable}{default}")
        
        # Get row count
        try:
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                print(f"\nRow Count: {count}")
                
                # Show sample data if table has data
                if count > 0:
                    print("\nSample Data (first 5 rows):")
                    result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 5"))
                    rows = result.fetchall()
                    for i, row in enumerate(rows, 1):
                        print(f"  Row {i}: {dict(row._mapping)}")
        except Exception as e:
            print(f"Error reading table data: {e}")
        
        print()

def view_registration_tables():
    """Focus on registration-related tables"""
    print("=" * 60)
    print("REGISTRATION-RELATED TABLES")
    print("=" * 60)
    
    load_dotenv()
    database_url = os.getenv("DATABASE_URL", "sqlite:///./bbpulse.db")
    engine = create_engine(database_url, echo=False)
    
    # Registration-related tables
    reg_tables = ['users', 'otp_records', 'organizations', 'organization_memberships', 'token_blacklist']
    
    for table_name in reg_tables:
        try:
            with engine.connect() as conn:
                # Check if table exists
                result = conn.execute(text(f"""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='{table_name}'
                """))
                if not result.fetchone():
                    print(f"Table '{table_name}' does not exist")
                    continue
                
                print(f"\n{'=' * 30}")
                print(f"TABLE: {table_name}")
                print(f"{'=' * 30}")
                
                # Get table schema
                result = conn.execute(text(f"PRAGMA table_info({table_name})"))
                columns = result.fetchall()
                
                print("Schema:")
                for col in columns:
                    cid, name, type_name, not_null, default_val, pk = col
                    nullable = "NOT NULL" if not_null else "NULL"
                    default = f" DEFAULT {default_val}" if default_val is not None else ""
                    primary = " PRIMARY KEY" if pk else ""
                    print(f"  - {name}: {type_name} {nullable}{default}{primary}")
                
                # Get row count and sample data
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                print(f"\nRow Count: {count}")
                
                if count > 0:
                    print("\nSample Data:")
                    result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 3"))
                    rows = result.fetchall()
                    for i, row in enumerate(rows, 1):
                        print(f"  Row {i}: {dict(row._mapping)}")
                        
        except Exception as e:
            print(f"Error accessing table {table_name}: {e}")

if __name__ == "__main__":
    print("Choose an option:")
    print("1. View all database tables")
    print("2. View registration-related tables only")
    print("3. Both")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        view_database_info()
    elif choice == "2":
        view_registration_tables()
    elif choice == "3":
        view_database_info()
        view_registration_tables()
    else:
        print("Invalid choice. Showing all tables...")
        view_database_info()


