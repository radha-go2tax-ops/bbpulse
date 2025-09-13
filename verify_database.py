#!/usr/bin/env python3
"""
Database verification script for the registration system.
This script checks if OTP records and user data are being stored correctly.
"""
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bbpulse.database import DATABASE_URL
from bbpulse.models import User, OTPRecord, Organization, OrganizationMembership

def verify_database():
    """Verify database tables and data."""
    print("🔍 BluBus Plus Database Verification")
    print("=" * 50)
    print(f"Database URL: {DATABASE_URL}")
    print()
    
    try:
        # Create engine and session
        engine = create_engine(DATABASE_URL, echo=False)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Check if tables exist
        print("📋 Checking table existence...")
        
        with engine.connect() as conn:
            # Check users table
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                );
            """))
            users_exists = result.scalar()
            print(f"  Users table: {'✅' if users_exists else '❌'}")
            
            # Check organizations table
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'organizations'
                );
            """))
            orgs_exists = result.scalar()
            print(f"  Organizations table: {'✅' if orgs_exists else '❌'}")
            
            # Check organization_memberships table
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'organization_memberships'
                );
            """))
            memberships_exists = result.scalar()
            print(f"  Organization memberships table: {'✅' if memberships_exists else '❌'}")
            
            # Check otp_records table
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'otp_records'
                );
            """))
            otp_exists = result.scalar()
            print(f"  OTP records table: {'✅' if otp_exists else '❌'}")
            
            # Check token_blacklist table
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'token_blacklist'
                );
            """))
            blacklist_exists = result.scalar()
            print(f"  Token blacklist table: {'✅' if blacklist_exists else '❌'}")
        
        print()
        
        # Check data in tables
        print("📊 Checking table data...")
        
        # Count users
        user_count = db.query(User).count()
        print(f"  Users: {user_count}")
        
        # Count organizations
        org_count = db.query(Organization).count()
        print(f"  Organizations: {org_count}")
        
        # Count OTP records
        otp_count = db.query(OTPRecord).count()
        print(f"  OTP records: {otp_count}")
        
        # Count memberships
        membership_count = db.query(OrganizationMembership).count()
        print(f"  Organization memberships: {membership_count}")
        
        print()
        
        # Show recent users
        if user_count > 0:
            print("👥 Recent users:")
            recent_users = db.query(User).order_by(User.created_at.desc()).limit(5).all()
            for user in recent_users:
                print(f"  - {user.full_name} ({user.email or user.mobile}) - {user.source}")
        
        # Show recent OTP records
        if otp_count > 0:
            print("\n📱 Recent OTP records:")
            recent_otps = db.query(OTPRecord).order_by(OTPRecord.created_at.desc()).limit(5).all()
            for otp in recent_otps:
                print(f"  - {otp.contact} ({otp.contact_type}) - {otp.purpose} - Used: {otp.is_used}")
        
        # Show organizations
        if org_count > 0:
            print("\n🏢 Organizations:")
            orgs = db.query(Organization).order_by(Organization.created_at.desc()).limit(5).all()
            for org in orgs:
                print(f"  - {org.name} (Owner: {org.user_id})")
        
        print()
        print("✅ Database verification completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False
    
    finally:
        if 'db' in locals():
            db.close()

def test_otp_flow():
    """Test OTP flow with database."""
    print("\n🧪 Testing OTP Flow...")
    
    try:
        engine = create_engine(DATABASE_URL, echo=False)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Create a test OTP record
        from bbpulse.models import ContactType
        from datetime import datetime, timedelta
        
        test_otp = OTPRecord(
            contact="test@example.com",
            contact_type=ContactType.EMAIL,
            otp_code="123456",
            purpose="test",
            expires_at=datetime.utcnow() + timedelta(minutes=5)
        )
        
        db.add(test_otp)
        db.commit()
        
        print("  ✅ Test OTP record created")
        
        # Retrieve the OTP record
        retrieved_otp = db.query(OTPRecord).filter(
            OTPRecord.contact == "test@example.com",
            OTPRecord.purpose == "test"
        ).first()
        
        if retrieved_otp:
            print(f"  ✅ OTP record retrieved: {retrieved_otp.otp_code}")
            
            # Mark as used
            retrieved_otp.is_used = True
            db.commit()
            print("  ✅ OTP record marked as used")
            
            # Clean up
            db.delete(retrieved_otp)
            db.commit()
            print("  ✅ Test OTP record cleaned up")
        else:
            print("  ❌ Failed to retrieve OTP record")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ OTP flow test failed: {e}")
        return False
    
    finally:
        if 'db' in locals():
            db.close()

def main():
    """Main function."""
    print("Starting database verification...")
    
    # Verify database structure and data
    if not verify_database():
        print("\n❌ Database verification failed!")
        sys.exit(1)
    
    # Test OTP flow
    if not test_otp_flow():
        print("\n❌ OTP flow test failed!")
        sys.exit(1)
    
    print("\n🎉 All database tests passed!")
    print("\nNext steps:")
    print("1. Run the registration verification: python verify_registration.py")
    print("2. Start the server: python -m uvicorn bbpulse.main:app --reload")
    print("3. Test the API endpoints manually or with the verification script")

if __name__ == "__main__":
    main()

