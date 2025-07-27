from typing import Optional
import os
from llama_index.core import Settings
from llama_index.llms.anthropic import Anthropic
from llama_index.core.llms import ChatMessage, MessageRole
from app.config import settings
from app.personality.prompts import SYSTEM_PROMPT


class AnthropicLLM:
    """Manages the Anthropic LLM integration with LlamaIndex."""
    
    def __init__(self):
        self.api_key = settings.anthropic_api_key
        self.llm = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the Anthropic LLM with LlamaIndex settings."""
        # Check if we should use mock LLM for testing
        if os.getenv("USE_MOCK_LLM", "").lower() == "true":
            from app.core.mock_llm import MockAnthropicLLM
            self.llm = MockAnthropicLLM(system_prompt=SYSTEM_PROMPT)
            print("🔧 Using Mock LLM for testing")
        else:
            self.llm = Anthropic(
                api_key=self.api_key,
                model="claude-sonnet-4-20250514",  # Using Claude Sonnet 4
                max_tokens=4096,
                temperature=0.7,  # Balanced for friendly conversation
                system_prompt=SYSTEM_PROMPT
            )
        
        # Set as default LLM for LlamaIndex
        Settings.llm = self.llm
        
        # Configure other LlamaIndex settings
        Settings.chunk_size = 1024
        Settings.chunk_overlap = 20
    
    def get_llm(self):
        """Get the configured Anthropic LLM instance."""
        return self.llm
    
    def create_chat_message(self, content: str, role: MessageRole = MessageRole.USER) -> ChatMessage:
        """Create a chat message with the specified role."""
        return ChatMessage(role=role, content=content)
    
    def get_streaming_response(self, messages: list[ChatMessage]):
        """Get a streaming response from the LLM."""
        return self.llm.stream_chat(messages)
    
    def get_response(self, messages: list[ChatMessage]):
        """Get a non-streaming response from the LLM."""
        return self.llm.chat(messages)
    
    def test_connection(self) -> bool:
        """Test the connection to Anthropic API."""
        try:
            test_message = [
                ChatMessage(role=MessageRole.USER, content="Hello! Please respond with a brief greeting.")
            ]
            response = self.llm.chat(test_message)
            return bool(response.message.content)
        except Exception as e:
            print(f"Anthropic API connection test failed: {e}")
            return False


# Global instance
anthropic_llm = AnthropicLLM()