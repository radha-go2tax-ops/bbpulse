#!/usr/bin/env python3
"""
OTP Verification Demo Script

This script demonstrates the complete OTP verification flow in the BluBus Pulse system.
It shows how to:
1. Send OTP via email or WhatsApp
2. Verify OTP codes
3. Handle different scenarios (valid, invalid, expired, etc.)

Usage:
    python otp_verification_demo.py
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"  # Adjust if your server runs on different port
API_BASE = f"{BASE_URL}/auth"

class OTPVerificationDemo:
    """Demo class for OTP verification functionality."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_contact = "test@example.com"
        self.test_phone = "+919876543210"
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def send_otp_email(self, contact: str, purpose: str = "registration") -> Dict[str, Any]:
        """Send OTP via email."""
        print(f"\n📧 Sending OTP via email to: {contact}")
        
        payload = {
            "contact": contact,
            "contact_type": "email",
            "purpose": purpose
        }
        
        try:
            response = await self.client.post(
                f"{API_BASE}/send-otp",
                json=payload
            )
            
            result = {
                "status_code": response.status_code,
                "response": response.json() if response.status_code < 500 else response.text
            }
            
            if response.status_code == 200:
                print(f"✅ OTP sent successfully: {result['response']['message']}")
            else:
                print(f"❌ Failed to send OTP: {result['response']}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error sending OTP: {e}")
            return {"error": str(e)}
    
    async def send_otp_whatsapp(self, phone: str, purpose: str = "registration") -> Dict[str, Any]:
        """Send OTP via WhatsApp."""
        print(f"\n📱 Sending OTP via WhatsApp to: {phone}")
        
        payload = {
            "contact": phone,
            "contact_type": "whatsapp",
            "purpose": purpose
        }
        
        try:
            response = await self.client.post(
                f"{API_BASE}/send-otp",
                json=payload
            )
            
            result = {
                "status_code": response.status_code,
                "response": response.json() if response.status_code < 500 else response.text
            }
            
            if response.status_code == 200:
                print(f"✅ OTP sent successfully: {result['response']['message']}")
            else:
                print(f"❌ Failed to send OTP: {result['response']}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error sending OTP: {e}")
            return {"error": str(e)}
    
    async def verify_otp(self, contact: str, contact_type: str, otp: str, purpose: str = "registration") -> Dict[str, Any]:
        """Verify OTP code."""
        print(f"\n🔐 Verifying OTP: {otp} for {contact} ({contact_type})")
        
        payload = {
            "contact": contact,
            "contact_type": contact_type,
            "otp": otp,
            "purpose": purpose
        }
        
        try:
            response = await self.client.post(
                f"{API_BASE}/verify-otp/registration",
                json=payload
            )
            
            result = {
                "status_code": response.status_code,
                "response": response.json() if response.status_code < 500 else response.text
            }
            
            if response.status_code == 200:
                print(f"✅ OTP verified successfully: {result['response']['message']}")
            else:
                print(f"❌ OTP verification failed: {result['response']}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error verifying OTP: {e}")
            return {"error": str(e)}
    
    async def login_with_otp(self, contact: str, contact_type: str, otp: str) -> Dict[str, Any]:
        """Login using OTP."""
        print(f"\n🔑 Logging in with OTP: {otp} for {contact} ({contact_type})")
        
        payload = {
            "contact": contact,
            "contact_type": contact_type,
            "otp": otp
        }
        
        try:
            response = await self.client.post(
                f"{API_BASE}/login/otp",
                json=payload
            )
            
            result = {
                "status_code": response.status_code,
                "response": response.json() if response.status_code < 500 else response.text
            }
            
            if response.status_code == 200:
                print(f"✅ Login successful: {result['response']['message']}")
                print(f"🔑 Access Token: {result['response']['data']['access_token'][:50]}...")
            else:
                print(f"❌ Login failed: {result['response']}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error during login: {e}")
            return {"error": str(e)}
    
    async def demo_complete_flow(self):
        """Demonstrate complete OTP flow."""
        print("🚀 Starting OTP Verification Demo")
        print("=" * 50)
        
        # Test 1: Send OTP via Email
        print("\n📧 TEST 1: Email OTP Flow")
        print("-" * 30)
        
        email_result = await self.send_otp_email(self.test_contact, "registration")
        
        if email_result.get("status_code") == 200:
            # In a real scenario, user would receive the OTP and enter it
            # For demo purposes, we'll simulate different scenarios
            print("\n🔍 Simulating OTP verification scenarios:")
            
            # Test valid OTP (this would fail in real scenario as we don't know the actual OTP)
            print("\n1. Testing with invalid OTP (expected to fail):")
            await self.verify_otp(self.test_contact, "email", "123456", "registration")
            
            print("\n2. Testing with another invalid OTP (expected to fail):")
            await self.verify_otp(self.test_contact, "email", "000000", "registration")
        
        # Test 2: Send OTP via WhatsApp
        print("\n\n📱 TEST 2: WhatsApp OTP Flow")
        print("-" * 30)
        
        whatsapp_result = await self.send_otp_whatsapp(self.test_phone, "registration")
        
        if whatsapp_result.get("status_code") == 200:
            print("\n🔍 Simulating WhatsApp OTP verification:")
            
            # Test invalid OTP
            print("\n1. Testing with invalid OTP (expected to fail):")
            await self.verify_otp(self.test_phone, "whatsapp", "999999", "registration")
        
        # Test 3: OTP Login Flow
        print("\n\n🔑 TEST 3: OTP Login Flow")
        print("-" * 30)
        
        # Send OTP for login
        login_otp_result = await self.send_otp_email(self.test_contact, "login")
        
        if login_otp_result.get("status_code") == 200:
            print("\n🔍 Simulating OTP login:")
            
            # Test login with invalid OTP
            print("\n1. Testing login with invalid OTP (expected to fail):")
            await self.login_with_otp(self.test_contact, "email", "111111")
        
        print("\n" + "=" * 50)
        print("✅ Demo completed!")
        print("\n📝 Notes:")
        print("- In a real application, users would receive actual OTP codes")
        print("- The OTP codes are 6 digits and expire in 5 minutes")
        print("- Users have a maximum of 3 attempts to enter the correct OTP")
        print("- After 3 failed attempts, the OTP becomes invalid")
        print("- OTPs are single-use and become invalid after successful verification")
    
    async def demo_error_scenarios(self):
        """Demonstrate various error scenarios."""
        print("\n\n🚨 ERROR SCENARIOS DEMO")
        print("=" * 50)
        
        # Test 1: Invalid contact type
        print("\n1. Testing with invalid contact type:")
        await self.send_otp_email("test@example.com", "invalid_type")
        
        # Test 2: Invalid email format
        print("\n2. Testing with invalid email format:")
        await self.send_otp_email("invalid-email", "registration")
        
        # Test 3: Rate limiting (if implemented)
        print("\n3. Testing rate limiting (sending multiple OTPs quickly):")
        for i in range(3):
            print(f"   Sending OTP #{i+1}...")
            await self.send_otp_email(f"test{i}@example.com", "registration")
            await asyncio.sleep(1)  # Small delay between requests
        
        # Test 4: Verifying OTP without sending one first
        print("\n4. Testing OTP verification without sending OTP first:")
        await self.verify_otp("nonexistent@example.com", "email", "123456", "registration")
        
        print("\n✅ Error scenarios demo completed!")

async def main():
    """Main demo function."""
    demo = OTPVerificationDemo()
    
    try:
        # Run the complete flow demo
        await demo.demo_complete_flow()
        
        # Run error scenarios demo
        await demo.demo_error_scenarios()
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
    finally:
        await demo.close()

if __name__ == "__main__":
    print("🔐 BluBus Pulse OTP Verification Demo")
    print("Make sure your server is running on http://localhost:8000")
    print("Press Ctrl+C to stop the demo\n")
    
    asyncio.run(main())
