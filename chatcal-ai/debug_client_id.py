#!/usr/bin/env python3
"""Debug what client ID is being used."""

import requests
import json

def debug_client_id():
    """Debug the client ID configuration."""
    print("🔍 Debugging Client ID Configuration")
    print("=" * 50)
    
    # Test the /auth/login endpoint and show actual client ID
    try:
        response = requests.get("https://chatcal-ai-432729289953.us-east1.run.app/auth/login")
        if response.status_code == 200:
            auth_data = response.json()
            auth_url = auth_data['auth_url']
            
            # Extract client ID from the URL
            if 'client_id=' in auth_url:
                client_id = auth_url.split('client_id=')[1].split('&')[0]
                print(f"📋 Current client ID in auth URL: {client_id}")
                
                if client_id == "432729289953-1di05ajntobgvv0aakgjahnrtp60491j.apps.googleusercontent.com":
                    print("✅ CORRECT: Using desired client ID!")
                    return True
                elif client_id == "20442616960-t6qd6ru3n9nj88tbd42qpkmhg6jp6851.apps.googleusercontent.com":
                    print("❌ WRONG: Using old/wrong client ID")
                    print("🔧 This suggests environment variable not taking effect")
                    return False
                else:
                    print(f"❓ UNKNOWN: Unexpected client ID: {client_id}")
                    return False
            else:
                print("❌ Could not extract client ID from auth URL")
                return False
        else:
            print(f"❌ Failed to get auth URL: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing auth endpoint: {e}")
        return False

if __name__ == "__main__":
    success = debug_client_id()
    
    if not success:
        print("\n🔧 Troubleshooting Steps:")
        print("1. Check if environment variable GOOGLE_CLIENT_ID is set correctly")
        print("2. Verify no hardcoded client IDs in source code")
        print("3. Ensure new deployment actually updated the running code")
        print("4. Force cold start to reload environment variables")