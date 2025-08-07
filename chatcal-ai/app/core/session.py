import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
import redis
import logging
from app.config import settings
from app.core.conversation import ConversationManager

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages user sessions with Redis backend and in-memory fallback."""
    
    def __init__(self):
        self.session_timeout = timedelta(minutes=settings.session_timeout_minutes)
        self.conversations: Dict[str, ConversationManager] = {}
        self.redis_client = None
        self.redis_available = False
        self.in_memory_sessions: Dict[str, Dict] = {}  # Fallback storage
        
        # Try to initialize Redis connection
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection with error handling."""
        try:
            self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            self.redis_available = True
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.warning(f"⚠️ Redis unavailable, using in-memory sessions: {e}")
            self.redis_available = False
    
    def _store_session(self, session_id: str, session_data: Dict) -> bool:
        """Store session data in Redis or memory fallback."""
        if self.redis_available:
            try:
                self.redis_client.setex(
                    f"session:{session_id}",
                    self.session_timeout,
                    json.dumps(session_data)
                )
                return True
            except Exception as e:
                logger.warning(f"Redis store failed, falling back to memory: {e}")
                self.redis_available = False
        
        # Fallback to in-memory storage
        session_data["expires_at"] = (datetime.utcnow() + self.session_timeout).isoformat()
        self.in_memory_sessions[session_id] = session_data
        return True
    
    def _get_session_data(self, session_id: str) -> Optional[Dict]:
        """Get session data from Redis or memory fallback."""
        if self.redis_available:
            try:
                data = self.redis_client.get(f"session:{session_id}")
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.warning(f"Redis get failed, checking memory: {e}")
                self.redis_available = False
        
        # Check in-memory storage
        if session_id in self.in_memory_sessions:
            session = self.in_memory_sessions[session_id]
            # Check if session expired
            if "expires_at" in session:
                expires_at = datetime.fromisoformat(session["expires_at"])
                if datetime.utcnow() > expires_at:
                    # Session expired, remove it
                    del self.in_memory_sessions[session_id]
                    return None
            return session
        
        return None
    
    def _delete_session_data(self, session_id: str) -> bool:
        """Delete session data from Redis or memory."""
        success = False
        
        if self.redis_available:
            try:
                result = self.redis_client.delete(f"session:{session_id}")
                success = bool(result)
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")
        
        # Also remove from memory
        if session_id in self.in_memory_sessions:
            del self.in_memory_sessions[session_id]
            success = True
            
        return success
    
    def create_session(self, user_data: Optional[Dict] = None) -> str:
        """Create a new session and return the session ID."""
        session_id = str(uuid.uuid4())
        session_data = {
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "user_data": user_data or {},
            "conversation_started": False
        }
        
        # Store using fallback system
        self._store_session(session_id, session_data)
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve session data using fallback system."""
        return self._get_session_data(session_id)
    
    def update_session(self, session_id: str, updates: Dict) -> bool:
        """Update session data."""
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        
        session_data.update(updates)
        session_data["last_activity"] = datetime.utcnow().isoformat()
        
        # Store updated session using fallback system
        return self._store_session(session_id, session_data)
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        # Remove using fallback system
        result = self._delete_session_data(session_id)
        
        # Remove from conversation memory
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
            print(f"🔄 SESSION DEBUG: Reusing existing conversation for session {session_id}")
            existing_conv = self.conversations[session_id]
            print(f"🔄 SESSION DEBUG: Existing user info: {existing_conv.agent.user_info}")
            print(f"🔄 SESSION DEBUG: Conversation history length: {len(existing_conv.agent.memory.get_all())}")
            self.update_session(session_id, {"last_activity": datetime.utcnow().isoformat()})
            return existing_conv
        
        # Create new conversation
        print(f"🆕 SESSION DEBUG: Creating NEW conversation for session {session_id}")
        conversation = ConversationManager(
            session_id=session_id,
            max_history=settings.max_conversation_history
        )
        print(f"🆕 SESSION DEBUG: New agent user info: {conversation.agent.user_info}")
        self.conversations[session_id] = conversation
        
        # Update session
        self.update_session(session_id, {
            "conversation_started": True,
            "last_activity": datetime.utcnow().isoformat()
        })
        
        return conversation
    
    def store_conversation_history(self, session_id: str) -> bool:
        """Store conversation history."""
        if session_id not in self.conversations:
            return False
        
        # For now, conversation history is kept in memory
        # In production, this could be enhanced to persist to database
        return True
    
    def get_conversation_history(self, session_id: str) -> Optional[Dict]:
        """Retrieve conversation history."""
        # For now, return basic session info
        if session_id in self.conversations:
            return {
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "messages": []  # Simplified for now
            }
        return None
    
    def extend_session(self, session_id: str) -> bool:
        """Extend session timeout."""
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        
        # Update last_activity to extend session
        return self.update_session(session_id, {"last_activity": datetime.utcnow().isoformat()})
    
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