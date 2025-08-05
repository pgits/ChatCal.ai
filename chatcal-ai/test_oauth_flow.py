#!/usr/bin/env python3
"""
Test OAuth flow with persistent refresh tokens.
This script helps test the new Secret Manager integration.
"""

import os
import json
import requests
from urllib.parse import parse_qs, urlparse

# Cloud Run service URL
SERVICE_URL = "https://chatcal-ai-432729289953.us-east1.run.app"

def test_oauth_flow():
    """Test the complete OAuth flow."""
    print("🔧 Testing OAuth Flow with Persistent Refresh Tokens")
    print("=" * 60)
    
    # Step 1: Get auth URL
    print("1. Getting authorization URL...")
    response = requests.get(f"{SERVICE_URL}/auth/login")
    if response.status_code == 200:
        auth_data = response.json()
        auth_url = auth_data['auth_url']
        state = auth_data['state']
        print(f"✅ Auth URL generated")
        print(f"State: {state}")
        
        # Extract and fix the redirect URI
        if "localhost" in auth_url:
            print("⚠️  Detected localhost redirect URI - this needs manual OAuth completion")
            print("📋 Manual Steps:")
            print("   1. Go to Google Cloud Console > APIs & Credentials > OAuth 2.0 Client IDs")
            print("   2. Add this redirect URI: https://chatcal-ai-432729289953.us-east1.run.app/auth/callback")
            print("   3. Or complete OAuth locally and manually save refresh token to Secret Manager")
            print()
            print(f"🔗 Auth URL: {auth_url}")
            return False
        else:
            print(f"🔗 Auth URL: {auth_url}")
            print("👆 Please visit this URL in your browser to complete OAuth")
            return True
    else:
        print(f"❌ Failed to get auth URL: {response.status_code}")
        return False

def check_auth_status():
    """Check current authentication status."""
    print("\n2. Checking authentication status...")
    response = requests.get(f"{SERVICE_URL}/auth/status")
    if response.status_code == 200:
        status = response.json()
        print(f"✅ Auth Status: {status}")
        return status.get('authenticated', False)
    else:
        print(f"❌ Failed to check auth status: {response.status_code}")
        return False

def test_calendar_access():
    """Test calendar access after authentication."""
    print("\n3. Testing calendar access...")
    response = requests.get(f"{SERVICE_URL}/calendar/availability")
    if response.status_code == 200:
        availability = response.json()
        print(f"✅ Calendar access working: {len(availability.get('available_slots', []))} slots found")
        return True
    else:
        print(f"❌ Calendar access failed: {response.status_code}")
        if response.status_code == 401:
            print("   This indicates authentication is required")
        return False

def test_persistent_tokens():
    """Test that tokens persist across container restarts."""
    print("\n4. Testing token persistence...")
    print("📋 To test persistence:")
    print("   1. Complete OAuth authentication first")
    print("   2. Force a new Cloud Run container instance")
    print("   3. Test calendar access again")
    print("   4. Should work without re-authentication")
    
    # Check if refresh token exists in Secret Manager
    try:
        import subprocess
        result = subprocess.run([
            'gcloud', 'secrets', 'versions', 'list', 'oauth-refresh-token',
            '--project=chatcal-ai-prod-monroe919', '--format=json'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            versions = json.loads(result.stdout)
            if versions:
                print(f"✅ Found {len(versions)} refresh token version(s) in Secret Manager")
                return True
            else:
                print("⚠️  No refresh token versions found in Secret Manager")
                return False
        else:
            print(f"❌ Failed to check Secret Manager: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error checking Secret Manager: {e}")
        return False

if __name__ == "__main__":
    print("🧪 ChatCal.ai OAuth Persistence Test")
    print("====================================")
    
    # Test the flow
    step1_success = test_oauth_flow()
    step2_authenticated = check_auth_status()
    
    if step2_authenticated:
        test_calendar_access()
        test_persistent_tokens()
    else:
        print("\n📝 Next Steps:")
        print("1. Complete OAuth authentication using the URL above")
        print("2. Re-run this script to test persistence")
    
    print("\n🏁 Test completed!")