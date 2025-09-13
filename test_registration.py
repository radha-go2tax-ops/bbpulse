#!/usr/bin/env python3
"""
Test script for the registration system.
This script demonstrates the complete registration and authentication flow.
"""
import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "SecurePass123!"
TEST_NAME = "Test User"
TEST_ORGANIZATION = "Test Organization"

class RegistrationTester:
    """Test class for registration system."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None
    
    def test_health_check(self) -> bool:
        """Test if the API is running."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ API is running")
                return True
            else:
                print(f"❌ API health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API health check error: {e}")
            return False
    
    def test_register_user(self, email: str, password: str, name: str, organization: str) -> bool:
        """Test user registration."""
        try:
            data = {
                "contact": email,
                "contact_type": "email",
                "password": password,
                "full_name": name,
                "organization_name": organization
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/register",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                result = response.json()
                print("✅ User registration successful")
                print(f"   Message: {result.get('message')}")
                return True
            else:
                print(f"❌ User registration failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False
    
    def test_send_otp(self, email: str) -> bool:
        """Test sending OTP."""
        try:
            data = {
                "contact": email,
                "contact_type": "email",
                "purpose": "registration"
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/send-otp",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ OTP sent successfully")
                print(f"   Message: {result.get('message')}")
                return True
            else:
                print(f"❌ OTP send failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ OTP send error: {e}")
            return False
    
    def test_verify_otp(self, email: str, otp: str) -> bool:
        """Test OTP verification."""
        try:
            data = {
                "contact": email,
                "contact_type": "email",
                "otp": otp,
                "purpose": "registration"
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/verify-otp/registration",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ OTP verification successful")
                print(f"   Message: {result.get('message')}")
                return True
            else:
                print(f"❌ OTP verification failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ OTP verification error: {e}")
            return False
    
    def test_password_login(self, email: str, password: str) -> bool:
        """Test password-based login."""
        try:
            data = {
                "contact": email,
                "contact_type": "email",
                "password": password
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/login/password",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Password login successful")
                print(f"   Message: {result.get('message')}")
                
                # Store tokens for later use
                token_data = result.get('data', {})
                self.access_token = token_data.get('access_token')
                self.refresh_token = token_data.get('refresh_token')
                
                return True
            else:
                print(f"❌ Password login failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Password login error: {e}")
            return False
    
    def test_otp_login(self, email: str, otp: str) -> bool:
        """Test OTP-based login."""
        try:
            data = {
                "contact": email,
                "contact_type": "email",
                "otp": otp
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/login/otp",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ OTP login successful")
                print(f"   Message: {result.get('message')}")
                
                # Store tokens for later use
                token_data = result.get('data', {})
                self.access_token = token_data.get('access_token')
                self.refresh_token = token_data.get('refresh_token')
                
                return True
            else:
                print(f"❌ OTP login failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ OTP login error: {e}")
            return False
    
    def test_get_profile(self) -> bool:
        """Test getting user profile."""
        if not self.access_token:
            print("❌ No access token available")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(
                f"{self.base_url}/auth/profile",
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Profile retrieved successfully")
                print(f"   User: {result.get('data', {}).get('full_name')}")
                return True
            else:
                print(f"❌ Profile retrieval failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Profile retrieval error: {e}")
            return False
    
    def test_refresh_token(self) -> bool:
        """Test token refresh."""
        if not self.refresh_token:
            print("❌ No refresh token available")
            return False
        
        try:
            data = {
                "refresh_token": self.refresh_token
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/refresh",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Token refresh successful")
                print(f"   Message: {result.get('message')}")
                
                # Update tokens
                token_data = result.get('data', {})
                self.access_token = token_data.get('access_token')
                self.refresh_token = token_data.get('refresh_token')
                
                return True
            else:
                print(f"❌ Token refresh failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Token refresh error: {e}")
            return False
    
    def test_logout(self) -> bool:
        """Test logout."""
        if not self.access_token:
            print("❌ No access token available")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/logout",
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Logout successful")
                print(f"   Message: {result.get('message')}")
                return True
            else:
                print(f"❌ Logout failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Logout error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests."""
        print("🚀 Starting Registration System Tests")
        print("=" * 50)
        
        # Test 1: Health Check
        print("\n1. Testing API Health Check...")
        if not self.test_health_check():
            print("❌ API is not running. Please start the server first.")
            return
        
        # Test 2: User Registration
        print("\n2. Testing User Registration...")
        if not self.test_register_user(TEST_EMAIL, TEST_PASSWORD, TEST_NAME, TEST_ORGANIZATION):
            print("❌ Registration failed. Stopping tests.")
            return
        
        # Test 3: Send OTP
        print("\n3. Testing OTP Send...")
        if not self.test_send_otp(TEST_EMAIL):
            print("❌ OTP send failed. Stopping tests.")
            return
        
        # Test 4: Verify OTP (Note: In real scenario, user would enter OTP from email)
        print("\n4. Testing OTP Verification...")
        print("   Note: In a real scenario, you would enter the OTP from your email.")
        print("   For testing purposes, we'll skip this step.")
        
        # Test 5: Password Login
        print("\n5. Testing Password Login...")
        if not self.test_password_login(TEST_EMAIL, TEST_PASSWORD):
            print("❌ Password login failed. Stopping tests.")
            return
        
        # Test 6: Get Profile
        print("\n6. Testing Profile Retrieval...")
        if not self.test_get_profile():
            print("❌ Profile retrieval failed. Stopping tests.")
            return
        
        # Test 7: Token Refresh
        print("\n7. Testing Token Refresh...")
        if not self.test_refresh_token():
            print("❌ Token refresh failed. Stopping tests.")
            return
        
        # Test 8: Logout
        print("\n8. Testing Logout...")
        if not self.test_logout():
            print("❌ Logout failed. Stopping tests.")
            return
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print("\nRegistration System Features Demonstrated:")
        print("  - User registration with email")
        print("  - OTP sending capability")
        print("  - Password-based authentication")
        print("  - JWT token management")
        print("  - Profile management")
        print("  - Token refresh")
        print("  - Secure logout")


def main():
    """Main function."""
    print("BluBus Plus Registration System Test")
    print("===================================")
    print(f"Testing against: {BASE_URL}")
    print(f"Test email: {TEST_EMAIL}")
    print(f"Test organization: {TEST_ORGANIZATION}")
    print()
    
    # Create tester instance
    tester = RegistrationTester(BASE_URL)
    
    # Run all tests
    tester.run_all_tests()


if __name__ == "__main__":
    main()
