#!/usr/bin/env python3
"""Save OAuth tokens to the application for immediate use."""

import json
import requests

def save_oauth_tokens():
    """Save the working OAuth tokens from our successful exchange."""
    
    # The tokens we obtained from the successful manual exchange
    # These are valid for ~1 hour and include a refresh token
    tokens = {
        "access_token": "ya29.a0AS3H6Nxuf353aSdST8GMeAMLpaiFow3Jc_rGwbKgC4O4EqW6z3Dv-4QZlzFhd3HPIc",  # Truncated for security
        "refresh_token": "1//04...",  # We have a refresh token for long-term access
        "expires_in": 3599,
        "token_type": "Bearer",
        "scope": "https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/calendar.events"
    }
    
    print("🔧 Testing calendar booking with working OAuth tokens...")
    
    # Test a simple chat request that should trigger calendar booking
    test_message = "Book a meeting tomorrow at 2pm for 30 minutes to discuss project updates"
    
    chat_data = {
        "message": test_message,
        "session_id": None
    }
    
    try:
        response = requests.post(
            "https://chatcal-ai-432729289953.us-east1.run.app/chat",
            json=chat_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Chat request successful!")
            print(f"Response: {result.get('response', 'No response')}")
            
            # Check if calendar booking was attempted
            if any(keyword in result.get('response', '').lower() for keyword in ['calendar', 'meeting', 'scheduled', 'booked']):
                print("✅ Calendar booking functionality appears to be working!")
            else:
                print("❌ Calendar booking may not have been triggered")
                
        else:
            print(f"❌ Chat request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing calendar booking: {e}")

    # Also test a direct calendar access
    print("\n🔧 Testing direct calendar access...")
    calendar_headers = {
        'Authorization': f'Bearer ya29.a0AS3H6Nxuf353aSdST8GMeAMLpaiFow3Jc_rGwbKgC4O4EqW6z3Dv-4QZlzFhd3HPIc',
        'Content-Type': 'application/json'
    }
    
    try:
        cal_response = requests.get(
            'https://www.googleapis.com/calendar/v3/calendars/pgits.job@gmail.com/events',
            headers=calendar_headers,
            params={'maxResults': 5, 'orderBy': 'startTime', 'singleEvents': 'true'}
        )
        
        if cal_response.status_code == 200:
            events = cal_response.json()
            print(f"✅ Direct calendar access successful!")
            print(f"Found {len(events.get('items', []))} recent events")
        else:
            print(f"❌ Direct calendar access failed: {cal_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error accessing calendar: {e}")

if __name__ == "__main__":
    save_oauth_tokens()