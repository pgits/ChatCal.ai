"""Cloud Run optimized session management without Redis dependency."""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import os

class CloudRunSessionManager:
    """
    Lightweight in-memory session management for Cloud Run.
    Designed for stateless containers with automatic scaling.
    """
    
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        self.cleanup_interval = 3600  # 1 hour cleanup
        self.session_timeout = 1800   # 30 minutes session timeout
        self.last_cleanup = datetime.utcnow()
        
    def create_session(self, user_data: Optional[Dict] = None) -> str:
        """Create a new session with optional user data."""
        session_id = self._generate_session_id()
        
        self.sessions[session_id] = {
            "session_id": session_id,
            "user_data": user_data or {},
            "conversation_history": [],
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "is_active": True
        }
        
        # Cleanup old sessions periodically
        self._cleanup_expired_sessions()
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data by ID."""
        if session_id not in self.sessions:
            return None
            
        session = self.sessions[session_id]
        
        # Check if session is expired
        last_activity = datetime.fromisoformat(session["last_activity"])
        if datetime.utcnow() - last_activity > timedelta(seconds=self.session_timeout):
            self.delete_session(session_id)
            return None
            
        # Update last activity
        session["last_activity"] = datetime.utcnow().isoformat()
        return session
    
    def update_session(self, session_id: str, data: Dict) -> bool:
        """Update session data."""
        if session_id not in self.sessions:
            return False
            
        self.sessions[session_id].update(data)
        self.sessions[session_id]["last_activity"] = datetime.utcnow().isoformat()
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def add_message(self, session_id: str, message: Dict) -> bool:
        """Add a message to conversation history."""
        session = self.get_session(session_id)
        if not session:
            return False
            
        session["conversation_history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            **message
        })
        
        # Keep only last 20 messages to control memory usage
        if len(session["conversation_history"]) > 20:
            session["conversation_history"] = session["conversation_history"][-20:]
            
        return True
    
    def get_conversation_history(self, session_id: str) -> Optional[Dict]:
        """Get conversation history for a session."""
        session = self.get_session(session_id)
        if not session:
            return None
            
        return {
            "session_id": session_id,
            "messages": session["conversation_history"],
            "created_at": session["created_at"]
        }
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        timestamp = str(datetime.utcnow().timestamp())
        random_data = os.urandom(16)
        combined = f"{timestamp}{random_data}".encode()
        return hashlib.sha256(combined).hexdigest()[:32]
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions to free memory."""
        now = datetime.utcnow()
        
        # Only cleanup every hour to avoid overhead
        if now - self.last_cleanup < timedelta(seconds=self.cleanup_interval):
            return
            
        expired_sessions = []
        for session_id, session in self.sessions.items():
            last_activity = datetime.fromisoformat(session["last_activity"])
            if now - last_activity > timedelta(seconds=self.session_timeout):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            
        self.last_cleanup = now
        
        # Log cleanup for monitoring
        if expired_sessions:
            print(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")
    
    def get_stats(self) -> Dict:
        """Get session manager statistics."""
        return {
            "active_sessions": len(self.sessions),
            "last_cleanup": self.last_cleanup.isoformat(),
            "memory_usage_estimate": len(json.dumps(self.sessions)) / 1024  # KB
        }

# Global instance for Cloud Run
cloudrun_session_manager = CloudRunSessionManager()