import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
import redis
from app.config import settings
from app.core.conversation import ConversationManager


class SessionManager:
    """Manages user sessions with Redis backend or in-memory fallback."""
    
    def __init__(self):
        self.session_timeout = timedelta(minutes=settings.session_timeout_minutes)
        self.conversations: Dict[str, ConversationManager] = {}
        self.use_redis = True
        self.memory_sessions: Dict[str, Dict] = {}  # Fallback storage
        
        # Force in-memory mode for Cloud Run deployment
        print("⚠️  Using in-memory sessions for Cloud Run deployment")
        self.use_redis = False
        self.redis_client = None
    
    def create_session(self, user_data: Optional[Dict] = None) -> str:
        """Create a new session and return the session ID."""
        session_id = str(uuid.uuid4())
        session_data = {
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "user_data": user_data or {},
            "conversation_started": False
        }
        
        if self.use_redis:
            # Store in Redis with expiration
            self.redis_client.setex(
                f"session:{session_id}",
                self.session_timeout,
                json.dumps(session_data)
            )
        else:
            # Store in memory
            self.memory_sessions[session_id] = session_data
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve session data from Redis or memory."""
        if self.use_redis:
            data = self.redis_client.get(f"session:{session_id}")
            if data:
                return json.loads(data)
        else:
            return self.memory_sessions.get(session_id)
        return None
    
    def update_session(self, session_id: str, updates: Dict) -> bool:
        """Update session data."""
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        
        session_data.update(updates)
        session_data["last_activity"] = datetime.utcnow().isoformat()
        
        if self.use_redis:
            # Reset expiration on activity
            self.redis_client.setex(
                f"session:{session_id}",
                self.session_timeout,
                json.dumps(session_data)
            )
        else:
            # Update in memory
            self.memory_sessions[session_id] = session_data
        
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        result = False
        
        if self.use_redis:
            # Remove from Redis
            result = bool(self.redis_client.delete(f"session:{session_id}"))
        else:
            # Remove from memory
            if session_id in self.memory_sessions:
                del self.memory_sessions[session_id]
                result = True
        
        # Remove from conversations memory
        if session_id in self.conversations:
            del self.conversations[session_id]
        
        return result
    
    def get_or_create_conversation(self, session_id: str) -> Optional[ConversationManager]:
        """Get or create a conversation manager for a session."""
        # Check if session exists
        if not self.get_session(session_id):
            return None
        
        # Return existing conversation if in memory
        if session_id in self.conversations:
            self.update_session(session_id, {"last_activity": datetime.utcnow().isoformat()})
            return self.conversations[session_id]
        
        # Create new conversation
        conversation = ConversationManager(
            session_id=session_id,
            max_history=settings.max_conversation_history
        )
        self.conversations[session_id] = conversation
        
        # Update session
        self.update_session(session_id, {
            "conversation_started": True,
            "last_activity": datetime.utcnow().isoformat()
        })
        
        return conversation
    
    def store_conversation_history(self, session_id: str) -> bool:
        """Store conversation history in Redis or memory."""
        if session_id not in self.conversations:
            return False
        
        conversation = self.conversations[session_id]
        # TODO: Fix export_conversation method to handle dict/object conversion
        # For now, just store basic session info
        history = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "messages": []  # Simplified for now
        }
        
        if self.use_redis:
            # Store conversation history separately
            self.redis_client.setex(
                f"conversation:{session_id}",
                self.session_timeout * 2,  # Keep conversation history longer
                json.dumps(history)
            )
        # For in-memory mode, we don't need separate conversation storage
        # since conversations are already in self.conversations
        
        return True
    
    def get_conversation_history(self, session_id: str) -> Optional[Dict]:
        """Retrieve conversation history from Redis or memory."""
        if self.use_redis:
            data = self.redis_client.get(f"conversation:{session_id}")
            if data:
                return json.loads(data)
        else:
            # For in-memory mode, return basic info if conversation exists
            if session_id in self.conversations:
                return {
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "messages": []  # Simplified
                }
        return None
    
    def extend_session(self, session_id: str) -> bool:
        """Extend session timeout."""
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        
        if self.use_redis:
            # Reset expiration
            self.redis_client.expire(f"session:{session_id}", self.session_timeout)
        # For in-memory mode, sessions don't expire automatically
        
        return True
    
    def cleanup_expired_conversations(self):
        """Clean up expired conversations from memory."""
        expired = []
        for session_id in self.conversations:
            if not self.get_session(session_id):
                expired.append(session_id)
        
        for session_id in expired:
            del self.conversations[session_id]


# Global session manager instance
session_manager = SessionManager()