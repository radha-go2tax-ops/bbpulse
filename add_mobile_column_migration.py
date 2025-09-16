#!/usr/bin/env python3
"""
Migration script to add mobile column to operator_users table.
This script will:
1. Connect to the PostgreSQL database
2. Add the mobile column to operator_users table
3. Add the mobile_verified column to operator_users table
4. Verify the migration
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from bbpulse.settings import settings

def get_database_engine():
    """Create PostgreSQL engine."""
    try:
        engine = create_engine(settings.database_url, echo=True)
        return engine
    except Exception as e:
        print(f"❌ Error creating database engine: {e}")
        return None

def add_mobile_columns(engine):
    """Add mobile and mobile_verified columns to operator_users table."""
    try:
        with engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()
            
            try:
                # Check if mobile column already exists
                check_mobile = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'operator_users' 
                    AND column_name = 'mobile'
                """)
                
                result = conn.execute(check_mobile).fetchone()
                if result:
                    print("✅ Mobile column already exists")
                else:
                    # Add mobile column
                    add_mobile = text("""
                        ALTER TABLE operator_users 
                        ADD COLUMN mobile VARCHAR(20) UNIQUE
                    """)
                    conn.execute(add_mobile)
                    print("✅ Added mobile column to operator_users table")
                
                # Check if mobile_verified column already exists
                check_mobile_verified = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'operator_users' 
                    AND column_name = 'mobile_verified'
                """)
                
                result = conn.execute(check_mobile_verified).fetchone()
                if result:
                    print("✅ Mobile_verified column already exists")
                else:
                    # Add mobile_verified column
                    add_mobile_verified = text("""
                        ALTER TABLE operator_users 
                        ADD COLUMN mobile_verified BOOLEAN DEFAULT FALSE
                    """)
                    conn.execute(add_mobile_verified)
                    print("✅ Added mobile_verified column to operator_users table")
                
                # Create index on mobile column for better performance
                create_index = text("""
                    CREATE INDEX IF NOT EXISTS idx_operator_users_mobile 
                    ON operator_users(mobile)
                """)
                conn.execute(create_index)
                print("✅ Created index on mobile column")
                
                # Commit the transaction
                trans.commit()
                print("✅ Migration completed successfully!")
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                print(f"❌ Error during migration: {e}")
                raise
                
    except SQLAlchemyError as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

def verify_migration(engine):
    """Verify that the migration was successful."""
    try:
        with engine.connect() as conn:
            # Check table structure
            check_structure = text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'operator_users' 
                AND column_name IN ('mobile', 'mobile_verified')
                ORDER BY column_name
            """)
            
            result = conn.execute(check_structure).fetchall()
            
            print("\n📋 Verification Results:")
            print("=" * 50)
            
            if result:
                for row in result:
                    print(f"Column: {row[0]}")
                    print(f"  Type: {row[1]}")
                    print(f"  Nullable: {row[2]}")
                    print(f"  Default: {row[3]}")
                    print()
            else:
                print("❌ No mobile columns found!")
                return False
                
            return True
            
    except Exception as e:
        print(f"❌ Error verifying migration: {e}")
        return False

def main():
    """Main migration function."""
    print("🚀 Starting migration to add mobile columns to operator_users table...")
    print("=" * 70)
    
    # Get database engine
    engine = get_database_engine()
    if not engine:
        print("❌ Failed to create database engine")
        return False
    
    # Test database connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Run migration
    if add_mobile_columns(engine):
        print("\n🔍 Verifying migration...")
        if verify_migration(engine):
            print("\n🎉 Migration completed successfully!")
            print("✅ operator_users table now has mobile and mobile_verified columns")
            return True
        else:
            print("\n❌ Migration verification failed")
            return False
    else:
        print("\n❌ Migration failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
