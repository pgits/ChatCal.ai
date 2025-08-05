#!/usr/bin/env python3
"""Debug script to check actual configuration values in production."""

import os
import sys

# Add current directory to path
sys.path.insert(0, '/Users/petergits/dev/chatCal.ai/chatcal-ai')

def debug_configuration():
    """Debug configuration loading."""
    print("🔧 Environment Variables:")
    print(f"GOOGLE_CLIENT_ID: {os.getenv('GOOGLE_CLIENT_ID', 'NOT_SET')}")
    print(f"GOOGLE_CLIENT_SECRET: {os.getenv('GOOGLE_CLIENT_SECRET', 'NOT_SET')}")
    print(f"ENVIRONMENT: {os.getenv('ENVIRONMENT', 'NOT_SET')}")
    print()
    
    try:
        from app.config import settings
        print("🔧 Settings Values:")
        print(f"settings.google_client_id: {settings.google_client_id}")
        print(f"settings.google_client_secret: {settings.google_client_secret}")
        print()
        
        from app.calendar.auth import CalendarAuth
        auth = CalendarAuth()
        print("🔧 CalendarAuth Values:")
        print(f"auth.client_id: {auth.client_id}")
        print(f"auth.client_secret: {auth.client_secret}")
        print(f"auth.redirect_uri: {auth.redirect_uri}")
        
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_configuration()