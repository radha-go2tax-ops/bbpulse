#!/usr/bin/env python3
"""
Interactive OTP Verification Test Script

This script provides an interactive way to test the OTP verification system.
Users can send OTPs and verify them step by step.

Usage:
    python interactive_otp_test.py
"""

import asyncio
import httpx
import json
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/auth"

class InteractiveOTPTester:
    """Interactive OTP testing class."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.current_contact = None
        self.current_contact_type = None
        self.current_purpose = None
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    def print_header(self, title: str):
        """Print a formatted header."""
        print("\n" + "=" * 60)
        print(f" {title}")
        print("=" * 60)
    
    def print_success(self, message: str):
        """Print success message."""
        print(f"✅ {message}")
    
    def print_error(self, message: str):
        """Print error message."""
        print(f"❌ {message}")
    
    def print_info(self, message: str):
        """Print info message."""
        print(f"ℹ️  {message}")
    
    async def check_server_status(self) -> bool:
        """Check if server is running."""
        try:
            response = await self.client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                self.print_success("Server is running and accessible")
                return True
            else:
                self.print_error(f"Server returned status {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Cannot connect to server: {e}")
            return False
    
    async def send_otp(self, contact: str, contact_type: str, purpose: str) -> bool:
        """Send OTP and return success status."""
        payload = {
            "contact": contact,
            "contact_type": contact_type,
            "purpose": purpose
        }
        
        try:
            response = await self.client.post(f"{API_BASE}/send-otp", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"OTP sent successfully: {data['message']}")
                self.current_contact = contact
                self.current_contact_type = contact_type
                self.current_purpose = purpose
                return True
            else:
                data = response.json() if response.status_code < 500 else response.text
                self.print_error(f"Failed to send OTP: {data}")
                return False
                
        except Exception as e:
            self.print_error(f"Error sending OTP: {e}")
            return False
    
    async def verify_otp(self, otp: str) -> bool:
        """Verify OTP and return success status."""
        if not self.current_contact:
            self.print_error("No OTP sent yet. Please send an OTP first.")
            return False
        
        payload = {
            "contact": self.current_contact,
            "contact_type": self.current_contact_type,
            "otp": otp,
            "purpose": self.current_purpose
        }
        
        try:
            response = await self.client.post(f"{API_BASE}/verify-otp/registration", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"OTP verified successfully: {data['message']}")
                return True
            else:
                data = response.json() if response.status_code < 500 else response.text
                self.print_error(f"OTP verification failed: {data}")
                return False
                
        except Exception as e:
            self.print_error(f"Error verifying OTP: {e}")
            return False
    
    async def login_with_otp(self, otp: str) -> bool:
        """Login with OTP and return success status."""
        if not self.current_contact:
            self.print_error("No OTP sent yet. Please send an OTP first.")
            return False
        
        payload = {
            "contact": self.current_contact,
            "contact_type": self.current_contact_type,
            "otp": otp
        }
        
        try:
            response = await self.client.post(f"{API_BASE}/login/otp", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Login successful: {data['message']}")
                if 'data' in data and 'access_token' in data['data']:
                    token = data['data']['access_token']
                    self.print_info(f"Access Token: {token[:50]}...")
                return True
            else:
                data = response.json() if response.status_code < 500 else response.text
                self.print_error(f"Login failed: {data}")
                return False
                
        except Exception as e:
            self.print_error(f"Error during login: {e}")
            return False
    
    def get_user_input(self, prompt: str, input_type: str = "string") -> str:
        """Get user input with validation."""
        while True:
            try:
                value = input(f"{prompt}: ").strip()
                
                if not value:
                    print("Please enter a value.")
                    continue
                
                if input_type == "email":
                    if "@" not in value or "." not in value:
                        print("Please enter a valid email address.")
                        continue
                
                elif input_type == "phone":
                    if not value.replace("+", "").replace("-", "").replace(" ", "").isdigit():
                        print("Please enter a valid phone number.")
                        continue
                
                elif input_type == "otp":
                    if not value.isdigit() or len(value) != 6:
                        print("Please enter a 6-digit OTP code.")
                        continue
                
                return value
                
            except KeyboardInterrupt:
                print("\n\nExiting...")
                exit(0)
            except Exception as e:
                print(f"Error: {e}")
    
    def get_contact_type(self) -> str:
        """Get contact type from user."""
        while True:
            print("\nSelect contact type:")
            print("1. Email")
            print("2. WhatsApp")
            
            choice = input("Enter choice (1 or 2): ").strip()
            
            if choice == "1":
                return "email"
            elif choice == "2":
                return "whatsapp"
            else:
                print("Please enter 1 or 2.")
    
    def get_purpose(self) -> str:
        """Get OTP purpose from user."""
        while True:
            print("\nSelect OTP purpose:")
            print("1. Registration")
            print("2. Login")
            print("3. Password Reset")
            print("4. Other")
            
            choice = input("Enter choice (1-4): ").strip()
            
            if choice == "1":
                return "registration"
            elif choice == "2":
                return "login"
            elif choice == "3":
                return "password_reset"
            elif choice == "4":
                return self.get_user_input("Enter custom purpose")
            else:
                print("Please enter 1, 2, 3, or 4.")
    
    async def run_interactive_test(self):
        """Run the interactive test session."""
        self.print_header("Interactive OTP Verification Test")
        
        # Check server status
        if not await self.check_server_status():
            return
        
        while True:
            try:
                print("\n" + "=" * 60)
                print(" OTP VERIFICATION MENU")
                print("=" * 60)
                print("1. Send OTP")
                print("2. Verify OTP")
                print("3. Login with OTP")
                print("4. Show current session info")
                print("5. Clear session")
                print("6. Exit")
                
                choice = input("\nEnter your choice (1-6): ").strip()
                
                if choice == "1":
                    await self.handle_send_otp()
                elif choice == "2":
                    await self.handle_verify_otp()
                elif choice == "3":
                    await self.handle_login_otp()
                elif choice == "4":
                    self.show_session_info()
                elif choice == "5":
                    self.clear_session()
                elif choice == "6":
                    self.print_info("Goodbye!")
                    break
                else:
                    print("Please enter a valid choice (1-6).")
                    
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                self.print_error(f"Unexpected error: {e}")
    
    async def handle_send_otp(self):
        """Handle send OTP option."""
        self.print_header("Send OTP")
        
        contact_type = self.get_contact_type()
        
        if contact_type == "email":
            contact = self.get_user_input("Enter email address", "email")
        else:
            contact = self.get_user_input("Enter phone number (with country code)", "phone")
        
        purpose = self.get_purpose()
        
        self.print_info(f"Sending OTP to {contact} via {contact_type} for {purpose}...")
        
        success = await self.send_otp(contact, contact_type, purpose)
        
        if success:
            self.print_info("You can now verify the OTP using option 2.")
        else:
            self.print_info("Please try again or check the server logs.")
    
    async def handle_verify_otp(self):
        """Handle verify OTP option."""
        self.print_header("Verify OTP")
        
        if not self.current_contact:
            self.print_error("No OTP session active. Please send an OTP first.")
            return
        
        self.print_info(f"Current session: {self.current_contact} ({self.current_contact_type})")
        
        otp = self.get_user_input("Enter the 6-digit OTP code", "otp")
        
        self.print_info("Verifying OTP...")
        
        success = await self.verify_otp(otp)
        
        if success:
            self.print_info("OTP verification completed successfully!")
        else:
            self.print_info("OTP verification failed. Please check the code and try again.")
    
    async def handle_login_otp(self):
        """Handle login with OTP option."""
        self.print_header("Login with OTP")
        
        if not self.current_contact:
            self.print_error("No OTP session active. Please send an OTP first.")
            return
        
        self.print_info(f"Current session: {self.current_contact} ({self.current_contact_type})")
        
        otp = self.get_user_input("Enter the 6-digit OTP code", "otp")
        
        self.print_info("Attempting login...")
        
        success = await self.login_with_otp(otp)
        
        if success:
            self.print_info("Login completed successfully!")
        else:
            self.print_info("Login failed. Please check the code and try again.")
    
    def show_session_info(self):
        """Show current session information."""
        self.print_header("Current Session Info")
        
        if self.current_contact:
            print(f"Contact: {self.current_contact}")
            print(f"Type: {self.current_contact_type}")
            print(f"Purpose: {self.current_purpose}")
        else:
            print("No active session. Send an OTP to start a session.")
    
    def clear_session(self):
        """Clear current session."""
        self.print_header("Clear Session")
        
        self.current_contact = None
        self.current_contact_type = None
        self.current_purpose = None
        
        self.print_success("Session cleared successfully!")

async def main():
    """Main function."""
    tester = InteractiveOTPTester()
    
    try:
        await tester.run_interactive_test()
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        await tester.close()

if __name__ == "__main__":
    print("🔐 BluBus Pulse Interactive OTP Verification Test")
    print("Make sure your server is running on http://localhost:8000")
    print("Press Ctrl+C to exit at any time\n")
    
    asyncio.run(main())
