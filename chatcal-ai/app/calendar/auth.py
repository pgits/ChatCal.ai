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

# Allow HTTP for local development (OAuth2 normally requires HTTPS)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


class CalendarAuth:
    """Handles Google Calendar OAuth2 authentication."""
    
    # OAuth2 scopes required for calendar access
    SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events'
    ]
    
    # Singleton pattern for shared credential storage
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CalendarAuth, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Only initialize once (singleton pattern)
        if CalendarAuth._initialized:
            return
        CalendarAuth._initialized = True
        
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        # Use Cloud Run URL for production, localhost for development
        if os.getenv('ENVIRONMENT') == 'production':
            self.redirect_uri = "https://chatcal-ai-432729289953.us-east1.run.app/auth/callback"
        else:
            self.redirect_uri = "http://localhost:8000/auth/callback"
        self.credentials_path = settings.google_credentials_path
        self._service = None
        self._cached_credentials = None  # For Cloud Run memory-based credential storage
    
    def create_auth_flow(self, state: Optional[str] = None) -> Flow:
        """Create OAuth2 flow for authentication."""
        client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [self.redirect_uri]
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
        flow = self.create_auth_flow(state)
        flow.fetch_token(authorization_response=authorization_response)
        
        credentials = flow.credentials
        self.save_credentials(credentials)
        
        return credentials
    
    def save_credentials(self, credentials: Credentials):
        """Save credentials to file for future use."""
        # For Cloud Run production, store in memory/session only since file system is ephemeral
        if os.getenv('ENVIRONMENT') == 'production':
            # Store credentials in class instance for session persistence
            # Note: This will only persist for the current container instance
            self._cached_credentials = credentials
            print("📝 Credentials cached in memory for Cloud Run session")
            return
            
        # For local development, save to file
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
        # For Cloud Run production, try to load from memory cache first
        if os.getenv('ENVIRONMENT') == 'production':
            if hasattr(self, '_cached_credentials') and self._cached_credentials:
                credentials = self._cached_credentials
                # Refresh if expired
                if credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                    self._cached_credentials = credentials
                    print("🔄 Refreshed cached credentials")
                return credentials
            print("⚠️ No cached credentials found in Cloud Run session")
            return None
        
        # For local development, load from file
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