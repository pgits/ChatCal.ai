"""Google Cloud Secret Manager integration for OAuth token storage."""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

try:
    from google.cloud import secretmanager
    from google.api_core import exceptions as gcp_exceptions
    SECRET_MANAGER_AVAILABLE = True
except ImportError:
    SECRET_MANAGER_AVAILABLE = False
    secretmanager = None
    gcp_exceptions = None

from app.config import settings

logger = logging.getLogger(__name__)


class SecretManagerService:
    """Handles OAuth token storage in Google Cloud Secret Manager."""
    
    def __init__(self):
        self.project_id = self._get_project_id()
        self.secret_name = "oauth-refresh-token"
        self.client = None
        self.available = False
        
        logger.info(f"🔍 SECRET_MANAGER_AVAILABLE: {SECRET_MANAGER_AVAILABLE}")
        
        if SECRET_MANAGER_AVAILABLE:
            try:
                self.client = secretmanager.SecretManagerServiceClient()
                self.available = True
                logger.info("✅ Secret Manager client initialized successfully!")
            except Exception as e:
                logger.warning(f"⚠️ Secret Manager unavailable: {e}")
                self.available = False
        else:
            logger.warning("⚠️ Google Cloud Secret Manager library not available")
    
    def _get_project_id(self) -> str:
        """Get the current GCP project ID."""
        try:
            import requests
            # Try to get project ID from metadata server (works in GCP environments)
            response = requests.get(
                'http://metadata.google.internal/computeMetadata/v1/project/project-id',
                headers={'Metadata-Flavor': 'Google'},
                timeout=2
            )
            if response.status_code == 200:
                return response.text
        except:
            pass
        
        # Fallback to hardcoded project ID
        return "chatcal-ai-prod-monroe919"
    
    def store_oauth_credentials(self, credentials_data: Dict[str, Any]) -> bool:
        """Store OAuth credentials in Secret Manager."""
        if not self.available:
            logger.warning("Secret Manager not available for storing credentials")
            return False
        
        try:
            # Only store essential refresh token data (not the full credentials)
            secret_data = {
                "refresh_token": credentials_data.get("refresh_token"),
                "client_id": credentials_data.get("client_id"),
                "client_secret": credentials_data.get("client_secret"),
                "token_uri": credentials_data.get("token_uri"),
                "scopes": credentials_data.get("scopes", []),
                "stored_at": datetime.utcnow().isoformat()
            }
            
            # Only store if we have a refresh token
            if not secret_data["refresh_token"]:
                logger.warning("No refresh token to store")
                return False
            
            secret_value = json.dumps(secret_data)
            
            # Create or update the secret
            parent = f"projects/{self.project_id}"
            secret_id = self.secret_name
            
            try:
                # Try to create the secret first
                secret = {
                    "replication": {"automatic": {}},
                }
                
                self.client.create_secret(
                    request={
                        "parent": parent,
                        "secret_id": secret_id,
                        "secret": secret,
                    }
                )
                logger.info(f"✅ Created new secret: {secret_id}")
                
            except gcp_exceptions.AlreadyExists:
                # Secret already exists, that's fine
                logger.info(f"Secret {secret_id} already exists")
            
            # Add a new version of the secret
            secret_name = f"{parent}/secrets/{secret_id}"
            response = self.client.add_secret_version(
                request={
                    "parent": secret_name,
                    "payload": {"data": secret_value.encode("UTF-8")},
                }
            )
            
            logger.info(f"✅ OAuth refresh token stored in Secret Manager: {response.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to store OAuth credentials in Secret Manager: {e}")
            return False
    
    def load_oauth_credentials(self) -> Optional[Dict[str, Any]]:
        """Load OAuth credentials from Secret Manager."""
        if not self.available:
            logger.warning("Secret Manager not available for loading credentials")
            return None
        
        try:
            # Access the latest version of the secret
            secret_name = f"projects/{self.project_id}/secrets/{self.secret_name}/versions/latest"
            
            response = self.client.access_secret_version(request={"name": secret_name})
            secret_value = response.payload.data.decode("UTF-8")
            
            credentials_data = json.loads(secret_value)
            logger.info("✅ OAuth credentials loaded from Secret Manager")
            
            return credentials_data
            
        except gcp_exceptions.NotFound:
            logger.info("No OAuth credentials found in Secret Manager")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to load OAuth credentials from Secret Manager: {e}")
            return None
    
    def delete_oauth_credentials(self) -> bool:
        """Delete OAuth credentials from Secret Manager."""
        if not self.available:
            logger.warning("Secret Manager not available for deleting credentials")
            return False
        
        try:
            secret_name = f"projects/{self.project_id}/secrets/{self.secret_name}"
            self.client.delete_secret(request={"name": secret_name})
            logger.info("✅ OAuth credentials deleted from Secret Manager")
            return True
            
        except gcp_exceptions.NotFound:
            logger.info("OAuth credentials not found in Secret Manager (already deleted)")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete OAuth credentials from Secret Manager: {e}")
            return False


# Global instance
secret_manager_service = SecretManagerService()