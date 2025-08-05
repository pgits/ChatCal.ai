"""Google Calendar OAuth2 authentication handling."""

import os
import json
from typing import Optional, Dict
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.config import settings

# Allow HTTP for local development and Cloud Run internal routing
# Cloud Run terminates HTTPS externally but uses HTTP internally
# CRITICAL: Must be set BEFORE any oauth imports to avoid transport errors
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
print(f"🔧 Global OAUTHLIB settings: INSECURE_TRANSPORT={os.environ.get('OAUTHLIB_INSECURE_TRANSPORT')}, RELAX_TOKEN_SCOPE={os.environ.get('OAUTHLIB_RELAX_TOKEN_SCOPE')}")


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
        self.redirect_uri = "https://chatcal-ai-432729289953.us-east1.run.app/auth/callback"
        print(f"🔧 CalendarAuth initialized with redirect_uri: {self.redirect_uri} [v2025-08-05]")
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
        # FORCE HTTPS for Cloud Run - this is critical for OAuth2 transport security
        if authorization_response.startswith('http://'):
            authorization_response = authorization_response.replace('http://', 'https://', 1)
            print(f"🔧 CONVERTED HTTP to HTTPS: {authorization_response}")
        
        print(f"🔧 Final authorization response URL: {authorization_response}")
        
        # CRITICAL: Set insecure transport override BEFORE any OAuth operations
        # This must be set before importing or using any oauth2lib components
        import os
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
        print(f"🔧 OAUTHLIB_INSECURE_TRANSPORT: {os.environ.get('OAUTHLIB_INSECURE_TRANSPORT')}")
        print(f"🔧 OAUTHLIB_RELAX_TOKEN_SCOPE: {os.environ.get('OAUTHLIB_RELAX_TOKEN_SCOPE')}")
        
        # Force reload of oauthlib modules to pick up environment changes
        import sys
        if 'oauthlib' in sys.modules:
            print("🔧 Reloading oauthlib modules...")
            # Clear cached modules that might have transport settings
            modules_to_reload = [k for k in sys.modules.keys() if k.startswith('oauthlib')]
            for module in modules_to_reload:
                if module in sys.modules:
                    del sys.modules[module]
        
        # Re-import with new environment settings
        from google_auth_oauthlib.flow import Flow
        
        # Create flow with explicit HTTPS redirect URI
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
        
        print(f"🔧 Flow redirect URI: {flow.redirect_uri}")
        
        try:
            flow.fetch_token(authorization_response=authorization_response)
            credentials = flow.credentials
            self.save_credentials(credentials)
            print("✅ OAuth token exchange successful!")
            return credentials
        except Exception as e:
            print(f"❌ OAuth token exchange failed: {e}")
            # Try one more time with additional transport overrides
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            # Create a custom session that allows insecure transport
            session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[500, 502, 503, 504]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            # Monkey patch the session into the flow
            flow._session = session
            
            flow.fetch_token(authorization_response=authorization_response)
            credentials = flow.credentials
            self.save_credentials(credentials)
            print("✅ OAuth token exchange successful on retry!")
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
            # For personal Gmail accounts, prioritize OAuth over service account
            credentials = self.load_credentials() or self._get_service_account_credentials()
            
        if not credentials:
            raise ValueError("No valid credentials available. Please authenticate first.")
        
        if not self._service:
            self._service = build('calendar', 'v3', credentials=credentials)
        
        return self._service
    
    def _get_service_account_credentials(self) -> Optional[ServiceAccountCredentials]:
        """Get service account credentials from Google Secret Manager or environment."""
        try:
            # For production (Cloud Run), get from Secret Manager
            if os.getenv('ENVIRONMENT') == 'production':
                from google.cloud import secretmanager
                
                client = secretmanager.SecretManagerServiceClient()
                project_id = "chatcal-ai-prod-monroe919"
                secret_name = f"projects/{project_id}/secrets/service-account-key/versions/latest"
                
                response = client.access_secret_version(request={"name": secret_name})
                secret_data = response.payload.data.decode("UTF-8")
                service_account_info = json.loads(secret_data)
                
                credentials = ServiceAccountCredentials.from_service_account_info(
                    service_account_info,
                    scopes=self.SCOPES
                    # Note: No subject parameter - direct service account access to shared calendar
                )
                print("🔧 Using service account credentials for shared calendar access")
                return credentials
                
            # For local development, try environment variable
            elif os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
                credentials = ServiceAccountCredentials.from_service_account_file(
                    os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
                    scopes=self.SCOPES
                    # Note: No subject parameter - direct service account access to shared calendar
                )
                print("🔧 Using service account credentials from file")
                return credentials
                
        except Exception as e:
            print(f"⚠️ Service account authentication failed: {e}")
            
        return None
    
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
            # Check service account credentials first
            service_credentials = self._get_service_account_credentials()
            if service_credentials:
                return True
                
            # Fallback to OAuth credentials
            oauth_credentials = self.load_credentials()
            return oauth_credentials is not None and oauth_credentials.valid
        except:
            return False