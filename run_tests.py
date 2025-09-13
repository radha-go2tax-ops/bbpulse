#!/usr/bin/env python3
"""
Test runner script for BluBus Plus.
"""
import os
import sys
import subprocess
import pytest
from pathlib import Path

def run_tests():
    """Run all tests with proper configuration."""
    # Set test environment
    os.environ["TESTING"] = "true"
    
    # Test directory
    test_dir = Path(__file__).parent / "tests"
    
    # Run tests with pytest
    test_args = [
        str(test_dir),
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--disable-warnings",  # Disable warnings
        "--color=yes",  # Colored output
        "-x",  # Stop on first failure
    ]
    
    print("🚀 Starting BluBus Plus Test Suite")
    print("=" * 50)
    
    try:
        result = pytest.main(test_args)
        
        if result == 0:
            print("\n✅ All tests passed!")
            return True
        else:
            print(f"\n❌ {result} test(s) failed!")
            return False
            
    except Exception as e:
        print(f"\n💥 Test runner error: {e}")
        return False

def run_specific_test(test_file: str):
    """Run a specific test file."""
    os.environ["TESTING"] = "true"
    
    test_path = Path(__file__).parent / "tests" / test_file
    
    if not test_path.exists():
        print(f"❌ Test file not found: {test_path}")
        return False
    
    print(f"🧪 Running {test_file}")
    print("=" * 50)
    
    try:
        result = pytest.main([str(test_path), "-v", "--tb=short", "--color=yes"])
        return result == 0
    except Exception as e:
        print(f"💥 Error running {test_file}: {e}")
        return False

def run_health_check():
    """Run a quick health check test."""
    print("🏥 Running Health Check")
    print("=" * 30)
    
    try:
        from blubuspulse.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test basic endpoints
        endpoints = [
            ("/", "Root endpoint"),
            ("/health/", "Health check"),
            ("/health/ready", "Readiness check"),
            ("/health/live", "Liveness check"),
        ]
        
        for endpoint, description in endpoints:
            try:
                response = client.get(endpoint)
                status = "✅" if response.status_code in [200, 401] else "❌"
                print(f"{status} {description}: {response.status_code}")
            except Exception as e:
                print(f"❌ {description}: Error - {e}")
        
        return True
        
    except Exception as e:
        print(f"💥 Health check failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "health":
            success = run_health_check()
        elif sys.argv[1].endswith(".py"):
            success = run_specific_test(sys.argv[1])
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Usage: python run_tests.py [health|test_file.py]")
            sys.exit(1)
    else:
        success = run_tests()
    
    sys.exit(0 if success else 1)
