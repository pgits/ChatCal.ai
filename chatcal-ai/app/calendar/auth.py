"""Google Calendar OAuth2 authentication handling."""

import os
import json
import redis
from typing import Optional, Dict
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.config import settings
from app.core.secrets import secret_manager_service


class CalendarAuth:
    """Handles Google Calendar OAuth2 authentication with Secret Manager storage."""
    
    # OAuth2 scopes required for calendar access
    SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events'
    ]
    
    def __init__(self):
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        
        # Force correct client ID if settings returns None or wrong value
        if not self.client_id or self.client_id != "432729289953-1di05ajntobgvv0aakgjahnrtp60491j.apps.googleusercontent.com":
            self.client_id = "432729289953-1di05ajntobgvv0aakgjahnrtp60491j.apps.googleusercontent.com"
            print(f"🔧 Forced correct client ID: {self.client_id}")
        
        # Debug logging for OAuth configuration
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🔐 OAuth Configuration: client_id={self.client_id[:20]}... (length: {len(self.client_id) if self.client_id else 0})")
        logger.info(f"🔐 Client secret configured: {bool(self.client_secret)}")
        
        # Always use production URL for OAuth since we're deploying to Cloud Run
        # For local development, you'll need to temporarily change this to localhost
        self.redirect_uri = "https://chatcal-ai-imoco2uwrq-ue.a.run.app/auth/callback"
        self.credentials_path = settings.google_credentials_path
        self._service = None
        
        # In-memory credential cache (persists for container lifetime)
        self._cached_credentials = None
        self._credentials_loaded_at = None
        
        # Redis client for session data (keeping for non-auth data)
        try:
            self.redis_client = redis.from_url(settings.redis_url)
            self.use_redis = True
        except:
            self.redis_client = None
            self.use_redis = False
    
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
        """Save credentials to Secret Manager (refresh token) and memory (access token)."""
        creds_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }
        
        # Primary storage: Secret Manager (for refresh token persistence)
        if secret_manager_service.available and credentials.refresh_token:
            try:
                secret_manager_service.store_oauth_credentials(creds_data)
                print("✅ OAuth refresh token saved to Secret Manager")
            except Exception as e:
                print(f"⚠️ Failed to save to Secret Manager (will try fallback): {e}")
        
        # In-memory cache: Store full credentials for container lifetime
        self._cached_credentials = credentials
        self._credentials_loaded_at = datetime.utcnow()
        print("✅ Credentials cached in memory for container lifetime")
        
        # Fallback storage: Redis (if available)
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.setex(
                    'google_calendar_credentials',
                    30 * 24 * 60 * 60,  # 30 days in seconds
                    json.dumps(creds_data)
                )
                print("✅ Credentials also saved to Redis (fallback)")
            except Exception as e:
                print(f"⚠️ Redis fallback failed: {e}")
        
        # Final fallback: Local file (temporary)
        try:
            os.makedirs(os.path.dirname(self.credentials_path), exist_ok=True)
            with open(self.credentials_path, 'w') as f:
                json.dump(creds_data, f)
            print("✅ Credentials also saved to local file (final fallback)")
        except Exception as e:
            print(f"⚠️ Local file fallback failed: {e}")
    
    def load_credentials(self) -> Optional[Credentials]:
        """Load credentials with optimized caching: Memory -> Secret Manager -> Fallbacks."""
        
        # 1. Try in-memory cache first (fastest, persists for container lifetime)
        if (self._cached_credentials and 
            self._credentials_loaded_at and 
            (datetime.utcnow() - self._credentials_loaded_at).total_seconds() < 3600):  # 1 hour cache
            
            # Check if cached credentials are still valid or can be refreshed
            if self._cached_credentials.valid:
                print("✅ Using cached credentials (in-memory)")
                return self._cached_credentials
            elif self._cached_credentials.refresh_token:
                try:
                    print("🔄 Refreshing cached credentials...")
                    self._cached_credentials.refresh(Request())
                    print("✅ Cached credentials refreshed successfully")
                    return self._cached_credentials
                except Exception as e:
                    print(f"⚠️ Failed to refresh cached credentials: {e}")
                    # Continue to Secret Manager lookup
        
        # 2. Try Secret Manager (persistent across container restarts)
        creds_data = None
        if secret_manager_service.available:
            try:
                secret_data = secret_manager_service.load_oauth_credentials()
                if secret_data:
                    # Reconstruct full credentials from stored refresh token data
                    credentials = Credentials(
                        token=None,  # Will be refreshed
                        refresh_token=secret_data.get('refresh_token'),
                        token_uri=secret_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
                        client_id=secret_data.get('client_id', self.client_id),
                        client_secret=secret_data.get('client_secret', self.client_secret),
                        scopes=secret_data.get('scopes', self.SCOPES)
                    )
                    
                    # Always refresh when loading from Secret Manager (access tokens expire)
                    if credentials.refresh_token:
                        try:
                            print("🔄 Refreshing credentials from Secret Manager...")
                            credentials.refresh(Request())
                            
                            # Cache the refreshed credentials
                            self._cached_credentials = credentials
                            self._credentials_loaded_at = datetime.utcnow()
                            
                            print("✅ Credentials loaded and refreshed from Secret Manager")
                            return credentials
                        except Exception as e:
                            print(f"❌ Failed to refresh Secret Manager credentials: {e}")
            except Exception as e:
                print(f"⚠️ Failed to load from Secret Manager: {e}")
        
        # 3. Fallback to Redis (if available)
        if self.use_redis and self.redis_client:
            try:
                redis_data = self.redis_client.get('google_calendar_credentials')
                if redis_data:
                    creds_data = json.loads(redis_data.decode('utf-8'))
                    print("✅ Credentials loaded from Redis (fallback)")
            except Exception as e:
                print(f"⚠️ Failed to load from Redis: {e}")
        
        # 4. Final fallback: Local file
        if not creds_data and os.path.exists(self.credentials_path):
            try:
                with open(self.credentials_path, 'r') as f:
                    creds_data = json.load(f)
                print("✅ Credentials loaded from local file (final fallback)")
            except Exception as e:
                print(f"⚠️ Failed to load from file: {e}")
        
        # Process fallback data if found
        if creds_data:
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
            
            # Refresh if expired and we have refresh token
            if credentials.expired and credentials.refresh_token:
                try:
                    print("🔄 Refreshing expired fallback credentials...")
                    credentials.refresh(Request())
                    # Save refreshed credentials to all storage locations
                    self.save_credentials(credentials)
                    print("✅ Fallback credentials refreshed and saved")
                except Exception as e:
                    print(f"❌ Failed to refresh fallback credentials: {e}")
                    return None
            
            # Cache the credentials
            self._cached_credentials = credentials
            self._credentials_loaded_at = datetime.utcnow()
            return credentials
        
        print("❌ No OAuth credentials found in any storage location")
        return None
    
    def get_calendar_service(self, credentials: Optional[Credentials] = None):
        """Get authenticated Google Calendar service."""
        if not credentials:
            credentials = self.load_credentials()
            
        if not credentials:
            raise ValueError("No valid credentials available. Please authenticate first.")
        
        # Check if credentials need refresh
        if not credentials.valid and credentials.refresh_token:
            try:
                print("🔄 Refreshing expired credentials for calendar service...")
                request = Request()
                credentials.refresh(request)
                print("✅ Successfully refreshed OAuth credentials for calendar service")
                
                # Save the refreshed credentials
                self.save_credentials(credentials)
                # Reset service to use new credentials
                self._service = None
            except Exception as e:
                print(f"❌ Failed to refresh credentials in calendar service: {e}")
                raise ValueError("Credentials expired and refresh failed. Please re-authenticate.")
        
        if not self._service:
            self._service = build('calendar', 'v3', credentials=credentials)
        
        return self._service
    
    def revoke_credentials(self):
        """Revoke stored credentials from all storage locations."""
        credentials = self.load_credentials()
        if credentials:
            try:
                credentials.revoke(Request())
            except:
                pass  # Ignore revocation errors
        
        # Clear in-memory cache
        self._cached_credentials = None
        self._credentials_loaded_at = None
        print("✅ Credentials cleared from memory cache")
        
        # Remove from Secret Manager
        if secret_manager_service.available:
            try:
                secret_manager_service.delete_oauth_credentials()
            except Exception as e:
                print(f"⚠️ Failed to remove from Secret Manager: {e}")
        
        # Remove from Redis
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.delete('google_calendar_credentials')
                print("✅ Credentials removed from Redis")
            except Exception as e:
                print(f"⚠️ Failed to remove from Redis: {e}")
        
        # Remove credentials file
        if os.path.exists(self.credentials_path):
            os.remove(self.credentials_path)
            print("✅ Credentials removed from local file")
        
        self._service = None
    
    def is_authenticated(self) -> bool:
        """Check if valid credentials exist, refreshing if necessary."""
        try:
            credentials = self.load_credentials()
            if not credentials:
                return False
            
            # If credentials are expired but we have a refresh token, try to refresh
            if not credentials.valid and credentials.refresh_token:
                try:
                    print("🔄 Access token expired, attempting refresh...")
                    request = Request()
                    credentials.refresh(request)
                    print("✅ Successfully refreshed OAuth credentials")
                    
                    # Save the refreshed credentials
                    self.save_credentials(credentials)
                    return True
                except Exception as e:
                    print(f"❌ Failed to refresh credentials: {e}")
                    return False
            
            return credentials.valid
        except Exception as e:
            print(f"❌ Error checking authentication: {e}")
            return False