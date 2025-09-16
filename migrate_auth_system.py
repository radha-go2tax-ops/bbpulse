#!/usr/bin/env python3
"""
Database migration script for the new authentication system.
This script creates the new tables for users, organizations, and related models.
"""
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bbpulse.database import DATABASE_URL, Base
from bbpulse.models import User, OTPRecord, TokenBlacklist

def create_tables():
    """Create all tables for the authentication system."""
    try:
        print("🔄 Creating authentication system tables...")
        
        # Create engine
        engine = create_engine(DATABASE_URL, echo=True)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ All tables created successfully!")
        
        # List created tables
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('users', 'organizations', 'organization_memberships', 'otp_records', 'token_blacklist')
                ORDER BY table_name;
            """))
            
            tables = [row[0] for row in result]
            
            if tables:
                print("\n📋 Created tables:")
                for table in tables:
                    print(f"  - {table}")
            else:
                print("\n⚠️  No authentication tables found. This might indicate an issue.")
        
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def verify_tables():
    """Verify that all required tables exist."""
    try:
        print("\n🔍 Verifying table structure...")
        
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Check users table
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'users'
                ORDER BY ordinal_position;
            """))
            
            users_columns = [row for row in result]
            
            if users_columns:
                print("✅ Users table structure:")
                for col in users_columns:
                    print(f"  - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            else:
                print("❌ Users table not found or empty")
                return False
            
            
            # Check otp_records table
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'otp_records'
                ORDER BY ordinal_position;
            """))
            
            otp_columns = [row for row in result]
            
            if otp_columns:
                print("✅ OTP records table structure:")
                for col in otp_columns:
                    print(f"  - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            else:
                print("❌ OTP records table not found or empty")
                return False
            
            # Check token_blacklist table
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'token_blacklist'
                ORDER BY ordinal_position;
            """))
            
            blacklist_columns = [row for row in result]
            
            if blacklist_columns:
                print("✅ Token blacklist table structure:")
                for col in blacklist_columns:
                    print(f"  - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            else:
                print("❌ Token blacklist table not found or empty")
                return False
        
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ Database verification error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected verification error: {e}")
        return False

def main():
    """Main function."""
    print("BluBus Plus Authentication System Migration")
    print("==========================================")
    print(f"Database URL: {DATABASE_URL}")
    print()
    
    # Create tables
    if not create_tables():
        print("\n❌ Migration failed!")
        sys.exit(1)
    
    # Verify tables
    if not verify_tables():
        print("\n❌ Table verification failed!")
        sys.exit(1)
    
    print("\n🎉 Migration completed successfully!")
    print("\nNext steps:")
    print("1. Start the FastAPI server: python -m uvicorn bbpulse.main:app --reload")
    print("2. Test the registration system: python test_registration.py")
    print("3. Check the API documentation: http://localhost:8000/docs")

if __name__ == "__main__":
    main()

