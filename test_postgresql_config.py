#!/usr/bin/env python3
"""
Test script to verify PostgreSQL configuration is working.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        from bbpulse.settings import settings
        print("✅ Settings imported successfully")
        print(f"   Database URL: {settings.database_url}")
        
        from bbpulse.database import engine, DATABASE_URL
        print("✅ Database module imported successfully")
        print(f"   DATABASE_URL: {DATABASE_URL}")
        
        from sqlalchemy import create_engine
        print("✅ SQLAlchemy imported successfully")
        
        import psycopg2
        print("✅ psycopg2 imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {str(e)}")
        return False

def test_database_connection():
    """Test database connection."""
    print("\n🔌 Testing database connection...")
    
    try:
        from bbpulse.database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            test_value = result.scalar()
            
        if test_value == 1:
            print("✅ Database connection successful")
            return True
        else:
            print(f"❌ Unexpected result: {test_value}")
            return False
            
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print("💡 This is expected if PostgreSQL is not running")
        return False

def test_models():
    """Test that models can be imported and defined."""
    print("\n📋 Testing models...")
    
    try:
        from bbpulse.models import Base
        print("✅ Models imported successfully")
        
        # Try to get table names
        from bbpulse.database import engine
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"   Found {len(tables)} tables: {tables}")
        
        return True
    except Exception as e:
        print(f"❌ Models error: {str(e)}")
        return False

def main():
    """Main test function."""
    print("🚀 PostgreSQL Configuration Test")
    print("=" * 40)
    
    # Test imports
    imports_ok = test_imports()
    
    # Test database connection
    connection_ok = test_database_connection()
    
    # Test models
    models_ok = test_models()
    
    print("\n📊 Test Summary:")
    print(f"   Imports: {'✅' if imports_ok else '❌'}")
    print(f"   Database Connection: {'✅' if connection_ok else '❌'}")
    print(f"   Models: {'✅' if models_ok else '❌'}")
    
    if imports_ok and models_ok:
        print("\n🎉 Configuration is correct!")
        if not connection_ok:
            print("💡 To test database connection, start PostgreSQL:")
            print("   docker run --name postgres-bbpulse -e POSTGRES_PASSWORD=password -e POSTGRES_DB=bbpulse -p 5432:5432 -d postgres:15-alpine")
        return True
    else:
        print("\n❌ Configuration has issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
