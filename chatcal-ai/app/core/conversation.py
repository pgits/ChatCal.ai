from typing import List, Dict, Optional
from datetime import datetime
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.memory import ChatMemoryBuffer
from app.core.agent import ChatCalAgent
# GREETING_TEMPLATES removed - no longer needed
import random


class ConversationManager:
    """Manages conversation state and memory for chat sessions."""
    
    def __init__(self, session_id: str, max_history: int = 20):
        self.session_id = session_id
        self.max_history = max_history
        self.agent = ChatCalAgent(session_id)
        self.conversation_started = False
    
    def start_conversation(self) -> str:
        """Start a new conversation with a friendly greeting."""
        if not self.conversation_started:
            greeting = self.agent.start_conversation()
            self.conversation_started = True
            return greeting
        return ""
    
    def get_response(self, user_input: str) -> str:
        """Get a response from the agent for the user input."""
        # Check for special commands first
        special_response = self.agent.handle_special_commands(user_input)
        if special_response:
            return special_response
        
        # Use the agent to handle the conversation
        return self.agent.chat(user_input)
    
    def get_streaming_response(self, user_input: str):
        """Get a streaming response from the agent for the user input."""
        # Check for special commands first
        special_response = self.agent.handle_special_commands(user_input)
        if special_response:
            # Stream the special response word by word
            for word in special_response.split():
                yield word + " "
            return
        
        # Use the agent's streaming capability
        for token in self.agent.stream_chat(user_input):
            yield token
    
    def clear_history(self):
        """Clear the conversation history."""
        self.agent.reset_conversation()
        self.conversation_started = False
    
    def get_conversation_history(self) -> List[Dict]:
        """Get the current conversation history."""
        return self.agent.get_conversation_history()
    
    def export_conversation(self) -> Dict:
        """Export the conversation for storage or analysis."""
        messages = self.get_conversation_history()
        return {
            "session_id": self.session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "messages": [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": getattr(msg, 'timestamp', None)
                }
                for msg in messages
            ]
        }