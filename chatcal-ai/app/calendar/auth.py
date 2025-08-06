"""Google Calendar OAuth2 authentication handling."""

import os
import json
from typing import Optional, Dict
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.config import settings


class CalendarAuth:
    """Handles Google Calendar OAuth2 authentication."""
    
    # OAuth2 scopes required for calendar access
    SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events'
    ]
    
    def __init__(self):
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        # Always use production URL for OAuth since we're deploying to Cloud Run
        # For local development, you'll need to temporarily change this to localhost
        self.redirect_uri = "https://chatcal-ai-imoco2uwrq-ue.a.run.app/auth/callback"
        self.credentials_path = settings.google_credentials_path
        self._service = None
    
    def create_auth_flow(self, state: Optional[str] = None) -> Flow:
        """Create OAuth2 flow for authentication."""
        # Simplified client config - only include essential fields
        client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            scopes=self.SCOPES,
            state=state
        )
        flow.redirect_uri = self.redirect_uri
        
        return flow
    
    def get_authorization_url(self, state: Optional[str] = None) -> tuple[str, str]:
        """Generate authorization URL for OAuth2 flow."""
        flow = self.create_auth_flow(state)
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent to get refresh token
        )
        
        return authorization_url, state
    
    def handle_callback(self, authorization_response: str, state: str) -> Credentials:
        """Handle OAuth2 callback and exchange code for credentials."""
        import requests
        from urllib.parse import urlparse, parse_qs
        from datetime import datetime, timedelta
        
        try:
            # Parse the authorization code from the response URL
            parsed_url = urlparse(authorization_response)
            query_params = parse_qs(parsed_url.query)
            auth_code = query_params.get('code', [None])[0]
            
            if not auth_code:
                raise Exception("No authorization code found in response")
            
            # Custom token exchange using direct HTTP request
            token_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': self.redirect_uri
            }
            
            import logging
            logging.info(f"Token exchange parameters: client_id={self.client_id[:20]}..., code={auth_code[:20]}..., redirect_uri={self.redirect_uri}")
            logging.info(f"Client secret length: {len(self.client_secret)}")
            
            response = requests.post(
                'https://oauth2.googleapis.com/token',
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code != 200:
                import logging
                logging.error(f"Token exchange HTTP status: {response.status_code}")
                logging.error(f"Token exchange response: {response.text}")
                raise Exception(f"Token exchange failed with status {response.status_code}: {response.text}")
            
            token_info = response.json()
            
            import logging
            logging.info(f"Token exchange successful! Received: {list(token_info.keys())}")
            
            # Create credentials object manually
            credentials = Credentials(
                token=token_info['access_token'],
                refresh_token=token_info.get('refresh_token'),
                token_uri='https://oauth2.googleapis.com/token',
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=self.SCOPES
            )
            
            # Set expiry if provided
            if 'expires_in' in token_info:
                expires_in = int(token_info['expires_in'])
                credentials.expiry = datetime.utcnow() + timedelta(seconds=expires_in)
            
            self.save_credentials(credentials)
            return credentials
            
        except Exception as e:
            import logging
            logging.error(f"Custom OAuth token exchange failed: {str(e)}")
            logging.error(f"Authorization response: {authorization_response}")
            logging.error(f"Client ID: {self.client_id}")
            logging.error(f"Redirect URI: {self.redirect_uri}")
            raise
    
    def save_credentials(self, credentials: Credentials):
        """Save credentials to file for future use."""
        os.makedirs(os.path.dirname(self.credentials_path), exist_ok=True)
        
        creds_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }
        
        with open(self.credentials_path, 'w') as f:
            json.dump(creds_data, f)
    
    def load_credentials(self) -> Optional[Credentials]:
        """Load saved credentials from file."""
        if not os.path.exists(self.credentials_path):
            return None
        
        with open(self.credentials_path, 'r') as f:
            creds_data = json.load(f)
        
        credentials = Credentials(
            token=creds_data['token'],
            refresh_token=creds_data.get('refresh_token'),
            token_uri=creds_data['token_uri'],
            client_id=creds_data['client_id'],
            client_secret=creds_data['client_secret'],
            scopes=creds_data['scopes']
        )
        
        # Set expiry if available
        if creds_data.get('expiry'):
            credentials.expiry = datetime.fromisoformat(creds_data['expiry'])
        
        # Refresh if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            self.save_credentials(credentials)
        
        return credentials
    
    def get_calendar_service(self, credentials: Optional[Credentials] = None):
        """Get authenticated Google Calendar service."""
        if not credentials:
            credentials = self.load_credentials()
            
        if not credentials:
            raise ValueError("No valid credentials available. Please authenticate first.")
        
        if not self._service:
            self._service = build('calendar', 'v3', credentials=credentials)
        
        return self._service
    
    def revoke_credentials(self):
        """Revoke stored credentials."""
        credentials = self.load_credentials()
        if credentials:
            try:
                credentials.revoke(Request())
            except:
                pass  # Ignore revocation errors
        
        # Remove credentials file
        if os.path.exists(self.credentials_path):
            os.remove(self.credentials_path)
        
        self._service = None
    
    def is_authenticated(self) -> bool:
        """Check if valid credentials exist."""
        try:
            credentials = self.load_credentials()
            return credentials is not None and credentials.valid
        except:
            return False