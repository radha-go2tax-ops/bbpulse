#!/usr/bin/env python3
"""
Migration script to move data from SQLite to PostgreSQL.
This script will:
1. Connect to both SQLite and PostgreSQL databases
2. Export data from SQLite
3. Import data into PostgreSQL
4. Verify the migration
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from bbpulse.models import Base
from bbpulse.settings import settings

def get_sqlite_engine():
    """Create SQLite engine for reading existing data."""
    sqlite_path = project_root / "bbpulse.db"
    if not sqlite_path.exists():
        print(f"❌ SQLite database not found at {sqlite_path}")
        return None
    
    sqlite_url = f"sqlite:///{sqlite_path}"
    return create_engine(sqlite_url)

def get_postgres_engine():
    """Create PostgreSQL engine for writing new data."""
    return create_engine(settings.database_url)

def migrate_table_data(sqlite_engine, postgres_engine, table_name):
    """Migrate data from SQLite table to PostgreSQL table."""
    try:
        # Read data from SQLite
        with sqlite_engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM {table_name}"))
            rows = result.fetchall()
            columns = result.keys()
        
        if not rows:
            print(f"  ⚠️  No data found in {table_name}")
            return True
        
        print(f"  📊 Found {len(rows)} rows in {table_name}")
        
        # Insert data into PostgreSQL
        with postgres_engine.connect() as conn:
            # Clear existing data
            conn.execute(text(f"DELETE FROM {table_name}"))
            conn.commit()
            
            # Insert new data
            for row in rows:
                row_dict = dict(zip(columns, row))
                # Convert None values to NULL for PostgreSQL
                for key, value in row_dict.items():
                    if value is None:
                        row_dict[key] = None
                
                # Build INSERT statement
                columns_str = ", ".join(columns)
                placeholders = ", ".join([f":{col}" for col in columns])
                insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                
                conn.execute(text(insert_sql), row_dict)
            
            conn.commit()
            print(f"  ✅ Successfully migrated {len(rows)} rows to {table_name}")
            return True
            
    except Exception as e:
        print(f"  ❌ Error migrating {table_name}: {str(e)}")
        return False

def verify_migration(sqlite_engine, postgres_engine):
    """Verify that the migration was successful."""
    print("\n🔍 Verifying migration...")
    
    try:
        # Get list of tables
        with sqlite_engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
            tables = [row[0] for row in result.fetchall()]
        
        all_good = True
        for table in tables:
            # Count rows in both databases
            with sqlite_engine.connect() as conn:
                sqlite_count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            
            with postgres_engine.connect() as conn:
                postgres_count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            
            if sqlite_count == postgres_count:
                print(f"  ✅ {table}: {sqlite_count} rows (matches)")
            else:
                print(f"  ❌ {table}: SQLite={sqlite_count}, PostgreSQL={postgres_count} (mismatch)")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"  ❌ Error during verification: {str(e)}")
        return False

def main():
    """Main migration function."""
    print("🚀 Starting migration from SQLite to PostgreSQL...")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if PostgreSQL is accessible
    try:
        postgres_engine = get_postgres_engine()
        with postgres_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ PostgreSQL connection successful")
    except Exception as e:
        print(f"❌ Cannot connect to PostgreSQL: {str(e)}")
        print("💡 Make sure PostgreSQL is running and accessible")
        return False
    
    # Check if SQLite database exists
    sqlite_engine = get_sqlite_engine()
    if not sqlite_engine:
        return False
    
    try:
        with sqlite_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ SQLite connection successful")
    except Exception as e:
        print(f"❌ Cannot connect to SQLite: {str(e)}")
        return False
    
    # Create PostgreSQL tables
    print("\n📋 Creating PostgreSQL tables...")
    try:
        Base.metadata.create_all(bind=postgres_engine)
        print("✅ PostgreSQL tables created successfully")
    except Exception as e:
        print(f"❌ Error creating PostgreSQL tables: {str(e)}")
        return False
    
    # Get list of tables to migrate
    with sqlite_engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
        tables = [row[0] for row in result.fetchall()]
    
    if not tables:
        print("⚠️  No tables found in SQLite database")
        return True
    
    print(f"\n📊 Found {len(tables)} tables to migrate: {', '.join(tables)}")
    
    # Migrate each table
    print("\n🔄 Migrating data...")
    success_count = 0
    for table in tables:
        print(f"\n📦 Migrating {table}...")
        if migrate_table_data(sqlite_engine, postgres_engine, table):
            success_count += 1
    
    print(f"\n📈 Migration Summary:")
    print(f"  ✅ Successfully migrated: {success_count}/{len(tables)} tables")
    
    if success_count == len(tables):
        # Verify migration
        if verify_migration(sqlite_engine, postgres_engine):
            print("\n🎉 Migration completed successfully!")
            print("💡 You can now update your .env file to use PostgreSQL")
            return True
        else:
            print("\n⚠️  Migration completed but verification failed")
            return False
    else:
        print(f"\n❌ Migration failed: {len(tables) - success_count} tables failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)



