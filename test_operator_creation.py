#!/usr/bin/env python3
"""
Test script to create a new operator account.
"""
import requests
import json
import time

def test_operator_creation():
    """Test creating a new operator account."""
    
    # First, let's try to start the simple FastAPI app
    print("Starting the application...")
    
    # The operator creation endpoint
    url = "http://localhost:8000/operators/"
    
    # Sample operator data
    operator_data = {
        "company_name": "Test Bus Company",
        "contact_email": "test@testbuscompany.com",
        "contact_phone": "+1-555-0123",
        "business_license": "BL123456789",
        "address": "123 Main Street",
        "city": "New York",
        "state": "NY",
        "country": "USA",
        "postal_code": "10001"
    }
    
    print(f"Attempting to create operator with data: {json.dumps(operator_data, indent=2)}")
    
    try:
        # Try to send the request
        response = requests.post(url, json=operator_data, timeout=10)
        
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 201:
            print("✅ Operator created successfully!")
            return response.json()
        else:
            print(f"❌ Failed to create operator: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the application. Make sure it's running on localhost:8000")
        return None
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    test_operator_creation()

