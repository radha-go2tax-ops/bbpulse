#!/usr/bin/env python3
"""
Complete verification runner for the registration system.
This script runs database migration, starts the server, and runs verification tests.
"""
import subprocess
import sys
import time
import os
import signal
from threading import Thread

def run_command(command, description):
    """Run a command and return success status."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed:")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False

def start_server():
    """Start the FastAPI server in the background."""
    print("🚀 Starting FastAPI server...")
    try:
        # Start server in background
        process = subprocess.Popen(
            ["python", "-m", "uvicorn", "bbpulse.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a bit for server to start
        time.sleep(5)
        
        # Check if server is running
        if process.poll() is None:
            print("✅ Server started successfully")
            return process
        else:
            print("❌ Server failed to start")
            return None
            
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return None

def stop_server(process):
    """Stop the FastAPI server."""
    if process:
        print("🛑 Stopping server...")
        process.terminate()
        process.wait()
        print("✅ Server stopped")

def main():
    """Main verification runner."""
    print("🎯 BluBus Plus Registration System Verification")
    print("=" * 60)
    
    server_process = None
    
    try:
        # Step 1: Run database migration
        if not run_command("python migrate_auth_system.py", "Database Migration"):
            print("❌ Migration failed. Please check your database configuration.")
            return False
        
        # Step 2: Verify database
        if not run_command("python verify_database.py", "Database Verification"):
            print("❌ Database verification failed.")
            return False
        
        # Step 3: Start server
        server_process = start_server()
        if not server_process:
            print("❌ Failed to start server.")
            return False
        
        # Step 4: Wait for server to be ready
        print("⏳ Waiting for server to be ready...")
        time.sleep(3)
        
        # Step 5: Run registration verification
        if not run_command("python verify_registration.py", "Registration Verification"):
            print("❌ Registration verification failed.")
            return False
        
        print("\n🎉 ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")
        print("\n📋 Summary:")
        print("  ✅ Database migration completed")
        print("  ✅ Database verification passed")
        print("  ✅ Server started successfully")
        print("  ✅ Registration system verified")
        print("  ✅ Email registration tested")
        print("  ✅ Mobile registration tested")
        print("  ✅ OTP system tested")
        print("  ✅ Authentication flows tested")
        print("  ✅ Rate limiting tested")
        print("  ✅ Input validation tested")
        
        print("\n🚀 Your registration system is ready!")
        print("\nNext steps:")
        print("1. The server is running at http://localhost:8000")
        print("2. View API docs at http://localhost:8000/docs")
        print("3. Test endpoints manually or use the verification scripts")
        print("4. Configure your email and WhatsApp services for production")
        
        # Keep server running
        print("\n⏳ Server is running. Press Ctrl+C to stop...")
        try:
            server_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
            stop_server(server_process)
        
        return True
        
    except KeyboardInterrupt:
        print("\n🛑 Verification interrupted by user")
        stop_server(server_process)
        return False
        
    except Exception as e:
        print(f"\n❌ Verification failed with error: {e}")
        stop_server(server_process)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

