#!/usr/bin/env python3
"""
Test different PostgreSQL connection configurations to find the right one.
"""

import psycopg2
from psycopg2 import sql
import sys

def test_connection(host, port, database, user, password):
    """Test a specific PostgreSQL connection."""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return True, version
    except Exception as e:
        return False, str(e)

def main():
    """Test various PostgreSQL connection configurations."""
    print("🔍 Testing PostgreSQL Connection Configurations")
    print("=" * 50)
    
    # Common configurations to test
    configs = [
        # (host, port, database, user, password, description)
        ("localhost", 5432, "bbpulse", "postgres", "password", "Default config"),
        ("localhost", 5432, "bbpulse", "postgres", "", "No password"),
        ("localhost", 5432, "postgres", "postgres", "password", "Default database"),
        ("localhost", 5432, "postgres", "postgres", "", "Default database, no password"),
        ("127.0.0.1", 5432, "bbpulse", "postgres", "password", "127.0.0.1 instead of localhost"),
        ("localhost", 5432, "bbpulse", "postgres", "postgres", "Password = username"),
        ("localhost", 5432, "bbpulse", "postgres", "admin", "Password = admin"),
    ]
    
    successful_configs = []
    
    for host, port, database, user, password, description in configs:
        print(f"\n🔌 Testing: {description}")
        print(f"   Host: {host}, Port: {port}, DB: {database}, User: {user}")
        
        success, result = test_connection(host, port, database, user, password)
        
        if success:
            print(f"   ✅ SUCCESS: {result[:50]}...")
            successful_configs.append((host, port, database, user, password, description))
        else:
            print(f"   ❌ FAILED: {result}")
    
    print(f"\n📊 Results: {len(successful_configs)} successful configuration(s)")
    
    if successful_configs:
        print("\n🎉 Working configurations:")
        for config in successful_configs:
            host, port, database, user, password, description = config
            print(f"   • {description}")
            print(f"     DATABASE_URL=postgresql://{user}:{password}@{host}:{port}/{database}")
        
        # Use the first successful configuration
        host, port, database, user, password, description = successful_configs[0]
        recommended_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        print(f"\n💡 Recommended configuration:")
        print(f"   DATABASE_URL={recommended_url}")
        
        return recommended_url
    else:
        print("\n❌ No working configurations found")
        print("\n💡 Please check:")
        print("   1. PostgreSQL is running")
        print("   2. Database 'bbpulse' exists")
        print("   3. User 'postgres' exists and has correct password")
        print("   4. PostgreSQL is listening on port 5432")
        return None

if __name__ == "__main__":
    recommended_url = main()
    if recommended_url:
        print(f"\n🔧 To update your .env file, run:")
        print(f"   (Get-Content .env) -replace 'DATABASE_URL=.*', 'DATABASE_URL={recommended_url}' | Set-Content .env")
    sys.exit(0 if recommended_url else 1)


