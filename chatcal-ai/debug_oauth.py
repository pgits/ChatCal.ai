#!/usr/bin/env python3
"""Debug script to check OAuth redirect URI configuration."""

import os
import sys

# Add current directory to path
sys.path.insert(0, '/Users/petergits/dev/chatCal.ai/chatcal-ai')

# Set environment to production to simulate Cloud Run
os.environ['ENVIRONMENT'] = 'production'

try:
    from app.calendar.auth import CalendarAuth
    
    print("🔧 Creating CalendarAuth instance...")
    auth = CalendarAuth()
    
    print(f"Redirect URI: {auth.redirect_uri}")
    print(f"Client ID: {auth.client_id[:20]}...")
    
    # Test creating auth flow
    print("\n🔧 Testing auth flow creation...")
    flow = auth.create_auth_flow()
    print(f"Flow redirect URI: {flow.redirect_uri}")
    
    # Get auth URL
    print("\n🔧 Getting authorization URL...")
    auth_url, state = auth.get_authorization_url()
    print(f"Auth URL redirect_uri parameter: {auth_url}")
    
    # Extract redirect URI from URL
    import urllib.parse
    parsed_url = urllib.parse.urlparse(auth_url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    redirect_uri = query_params.get('redirect_uri', ['Not found'])[0]
    
    print(f"Extracted redirect URI: {redirect_uri}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()