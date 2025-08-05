#!/usr/bin/env python3
"""Test script to verify OAuth2 authentication is working."""

import requests
import json

def test_oauth_authentication():
    """Test OAuth2 authentication flow."""
    base_url = "https://chatcal-ai-432729289953.us-east1.run.app"
    
    print("🔧 Testing OAuth2 authentication...")
    
    # Test auth status
    try:
        print("\n1. Checking current auth status...")
        response = requests.get(f"{base_url}/auth/status")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.json().get("authenticated"):
            print("✅ Already authenticated!")
            return test_calendar_access(base_url)
        else:
            print("❌ Not authenticated. Please visit the auth URL first.")
            
        # Get auth URL
        print("\n2. Getting authentication URL...")
        response = requests.get(f"{base_url}/auth/login")
        print(f"Status Code: {response.status_code}")
        auth_data = response.json()
        print(f"Auth URL: {auth_data.get('auth_url')}")
        
        print(f"\n📝 Next steps:")
        print(f"1. Visit: {auth_data.get('auth_url')}")
        print(f"2. Sign in with pgits.job@gmail.com")
        print(f"3. Grant calendar permissions")
        print(f"4. Run this test again")
        
        return False
        
    except Exception as e:
        print(f"❌ OAuth test failed: {e}")
        return False

def test_calendar_access(base_url):
    """Test calendar access after authentication."""
    try:
        print("\n3. Testing calendar access...")
        
        # Test debug endpoint
        response = requests.get(f"{base_url}/debug/calendar")
        print(f"Debug Status Code: {response.status_code}")
        print(f"Debug Response: {json.dumps(response.json(), indent=2)}")
        
        # Test a simple booking attempt
        print("\n4. Testing booking flow...")
        test_message = "Book a meeting for tomorrow at 2pm for 30 minutes"
        
        response = requests.post(f"{base_url}/chat", json={
            "message": test_message,
            "session_id": None
        })
        
        print(f"Booking Status Code: {response.status_code}")
        if response.status_code == 200:
            chat_response = response.json()
            print(f"Booking Response: {chat_response.get('response')}")
            return True
        else:
            print(f"Booking failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Calendar access test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_oauth_authentication()
    print(f"\n🎯 Overall test result: {'SUCCESS' if success else 'NEEDS_AUTH'}")