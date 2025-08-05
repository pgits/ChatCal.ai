#!/usr/bin/env python3
"""Quick OAuth test using the current client ID configuration."""

import requests
import json

SERVICE_URL = "https://chatcal-ai-432729289953.us-east1.run.app"

def test_current_setup():
    """Test OAuth with whatever client ID is currently configured."""
    print("🧪 Testing Current OAuth Setup")
    print("=" * 40)
    
    # Get current auth URL
    response = requests.get(f"{SERVICE_URL}/auth/login")
    if response.status_code == 200:
        auth_data = response.json()
        auth_url = auth_data['auth_url']
        state = auth_data['state']
        
        # Extract client ID from URL
        if 'client_id=' in auth_url:
            client_id = auth_url.split('client_id=')[1].split('&')[0]
            print(f"✅ Current Client ID: {client_id}")
            
            if '432729289953' in client_id:
                print("✅ Using correct client ID!")
                print(f"📋 Add this redirect URI to OAuth client:")
                print(f"   https://chatcal-ai-432729289953.us-east1.run.app/auth/callback")
                print()
                print(f"🔗 Then visit: {auth_url}")
                return True
            else:
                print(f"⚠️  Using wrong client ID: {client_id}")
                print(f"📋 Add this redirect URI to OAuth client {client_id}:")
                print(f"   https://chatcal-ai-432729289953.us-east1.run.app/auth/callback")
                print()
                print(f"🔗 Then visit: {auth_url}")
                return False
    else:
        print(f"❌ Failed to get auth URL: {response.status_code}")
        return False

if __name__ == "__main__":
    test_current_setup()