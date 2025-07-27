#!/usr/bin/env python3
"""Complete OAuth2 authentication manually."""

import sys
from urllib.parse import urlparse, parse_qs
from app.calendar.auth import CalendarAuth

def complete_oauth_from_url(redirect_url):
    """Complete OAuth from the redirect URL."""
    print("🔐 Completing OAuth2 Authentication")
    print("=" * 50)
    
    try:
        # Parse the URL
        parsed = urlparse(redirect_url)
        params = parse_qs(parsed.query)
        
        # Extract code and state
        code = params.get('code', [None])[0]
        state = params.get('state', [None])[0]
        
        if not code:
            print("❌ No authorization code found in URL")
            return False
        
        print(f"✅ Found authorization code: {code[:20]}...")
        print(f"✅ State: {state}")
        
        # Complete authentication
        auth = CalendarAuth()
        
        # We'll use the full URL as authorization response
        auth_response = redirect_url
        
        # Try to complete the auth flow
        try:
            # For manual completion, we'll directly exchange the code
            from google_auth_oauthlib.flow import Flow
            
            # Create flow
            flow = auth.create_auth_flow(state)
            
            # Manually set the code
            flow.code = code
            
            # Fetch token
            flow.fetch_token(code=code)
            
            # Save credentials
            credentials = flow.credentials
            auth.save_credentials(credentials)
            
            print("✅ Authentication successful!")
            print(f"✅ Access token obtained: {credentials.token[:20]}...")
            print(f"✅ Refresh token: {'Yes' if credentials.refresh_token else 'No'}")
            print(f"✅ Credentials saved!")
            
            # Test the credentials
            service = auth.get_calendar_service()
            if service:
                print("\n📅 Testing calendar access...")
                calendar_list = service.calendarList().list().execute()
                print(f"✅ Found {len(calendar_list.get('items', []))} calendars")
                for cal in calendar_list.get('items', [])[:3]:
                    print(f"   - {cal.get('summary', 'Unnamed')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error exchanging code: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error parsing URL: {e}")
        return False

if __name__ == "__main__":
    print("📋 OAuth2 Manual Completion Tool")
    print()
    
    if len(sys.argv) > 1:
        # URL provided as argument
        redirect_url = sys.argv[1]
    else:
        # Ask for URL
        print("After authorizing the app, you were redirected to a URL.")
        print("Please paste the FULL redirect URL here:")
        print("(It should start with http://localhost:8000/auth/callback?code=...)")
        print()
        redirect_url = input("Paste URL here: ").strip()
    
    if redirect_url:
        if complete_oauth_from_url(redirect_url):
            print("\n✅ Setup complete! Your calendar is now connected.")
            print("You can now use ChatCal.ai to manage your calendar!")
        else:
            print("\n❌ Setup failed. Please try again.")
    else:
        print("❌ No URL provided")