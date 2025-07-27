#!/usr/bin/env python3
"""Test script to verify Google Calendar OAuth2 setup."""

import requests
import json

BASE_URL = "http://localhost:8080"

def check_auth_status():
    """Check if we're authenticated."""
    response = requests.get(f"{BASE_URL}/auth/status")
    data = response.json()
    print(f"📊 Authentication Status: {data}")
    return data.get("authenticated", False)

def test_calendar_integration():
    """Test calendar functionality."""
    # Create a session
    session_response = requests.post(f"{BASE_URL}/sessions", json={"user_data": {"name": "oauth_test"}})
    session_id = session_response.json()["session_id"]
    
    # Test calendar request
    chat_response = requests.post(f"{BASE_URL}/chat", json={
        "message": "What's on my calendar for today?",
        "session_id": session_id
    })
    
    if chat_response.status_code == 200:
        response_text = chat_response.json()["response"]
        print(f"✅ Calendar Query Response: {response_text[:200]}...")
        return True
    else:
        print(f"❌ Calendar Query Failed: {chat_response.text}")
        return False

def main():
    print("🔍 Testing Google Calendar OAuth2 Setup")
    print("=" * 50)
    
    if check_auth_status():
        print("✅ Already authenticated! Testing calendar integration...")
        test_calendar_integration()
    else:
        print("❌ Not authenticated yet.")
        print("Please complete the OAuth2 flow first:")
        print(f"1. Visit: {BASE_URL}/auth/login")
        print("2. Follow the authorization steps")
        print("3. Run this script again")

if __name__ == "__main__":
    main()