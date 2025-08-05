#!/usr/bin/env python3
"""Generate OAuth URL manually with correct credentials."""

import urllib.parse
import secrets
import string

def generate_oauth_url():
    """Generate OAuth URL with correct production credentials."""
    # Production OAuth client credentials
    client_id = "432729289953-1di05ajntobgvv0aakgjahnrtp60491j.apps.googleusercontent.com"
    redirect_uri = "https://chatcal-ai-432729289953.us-east1.run.app/auth/callback"
    scopes = [
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/calendar.events"
    ]
    
    # Generate secure random state
    alphabet = string.ascii_letters + string.digits + '-_'
    state = ''.join(secrets.choice(alphabet) for _ in range(43))
    
    # Build OAuth URL parameters
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': ' '.join(scopes),
        'access_type': 'offline',
        'include_granted_scopes': 'true',
        'prompt': 'consent',
        'state': state
    }
    
    # Generate OAuth URL
    base_url = "https://accounts.google.com/o/oauth2/auth"
    oauth_url = f"{base_url}?" + urllib.parse.urlencode(params)
    
    print("🚀 MANUAL OAuth URL (Production-Ready):")
    print(f"Client ID: {client_id}")
    print(f"Redirect URI: {redirect_uri}")
    print(f"State: {state}")
    print()
    print("OAuth URL:")
    print(oauth_url)
    print()
    print("📝 Test Instructions:")
    print("1. Visit the OAuth URL above")
    print("2. Sign in with pgits.job@gmail.com")
    print("3. Grant calendar permissions")
    print("4. You should be redirected to the production callback")
    print("5. Check if authentication succeeds with HTTPS transport fix")

if __name__ == "__main__":
    generate_oauth_url()