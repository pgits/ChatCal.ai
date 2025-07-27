import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
import redis
from app.config import settings
from app.core.conversation import ConversationManager


class SessionManager:
    """Manages user sessions with Redis backend."""
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        self.session_timeout = timedelta(minutes=settings.session_timeout_minutes)
        self.conversations: Dict[str, ConversationManager] = {}
    
    def create_session(self, user_data: Optional[Dict] = None) -> str:
        """Create a new session and return the session ID."""
        session_id = str(uuid.uuid4())
        session_data = {
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "user_data": user_data or {},
            "conversation_started": False
        }
        
        # Store in Redis with expiration
        self.redis_client.setex(
            f"session:{session_id}",
            self.session_timeout,
            json.dumps(session_data)
        )
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve session data from Redis."""
        data = self.redis_client.get(f"session:{session_id}")
        if data:
            return json.loads(data)
        return None
    
    def update_session(self, session_id: str, updates: Dict) -> bool:
        """Update session data."""
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        
        session_data.update(updates)
        session_data["last_activity"] = datetime.utcnow().isoformat()
        
        # Reset expiration on activity
        self.redis_client.setex(
            f"session:{session_id}",
            self.session_timeout,
            json.dumps(session_data)
        )
        
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        # Remove from Redis
        result = self.redis_client.delete(f"session:{session_id}")
        
        # Remove from memory
        if session_id in self.conversations:
            del self.conversations[session_id]
        
        return bool(result)
    
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
        """Store conversation history in Redis."""
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
        
        # Store conversation history separately
        self.redis_client.setex(
            f"conversation:{session_id}",
            self.session_timeout * 2,  # Keep conversation history longer
            json.dumps(history)
        )
        
        return True
    
    def get_conversation_history(self, session_id: str) -> Optional[Dict]:
        """Retrieve conversation history from Redis."""
        data = self.redis_client.get(f"conversation:{session_id}")
        if data:
            return json.loads(data)
        return None
    
    def extend_session(self, session_id: str) -> bool:
        """Extend session timeout."""
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        
        # Reset expiration
        self.redis_client.expire(f"session:{session_id}", self.session_timeout)
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