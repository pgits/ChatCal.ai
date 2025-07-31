"""Anthropic LLM integration for ChatCal.ai."""

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
        try:
            # Validate API key
            if not self.api_key or self.api_key == "your_anthropic_api_key_here":
                raise ValueError("Anthropic API key not configured. Please set ANTHROPIC_API_KEY in .env file")
            
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
                print("🔧 Using Anthropic Claude Sonnet 4 LLM")
            
            # Set as default LLM for LlamaIndex
            Settings.llm = self.llm
            
            # Configure other LlamaIndex settings
            Settings.chunk_size = 1024
            Settings.chunk_overlap = 20
            
        except Exception as e:
            print(f"❌ Failed to initialize Anthropic LLM: {e}")
            # Fallback to mock LLM if available
            try:
                from app.core.mock_llm import MockAnthropicLLM
                self.llm = MockAnthropicLLM(system_prompt=SYSTEM_PROMPT)
                print("🔧 Falling back to Mock LLM")
            except ImportError:
                raise RuntimeError(f"Failed to initialize Anthropic LLM and no fallback available: {e}")
    
    def get_llm(self):
        """Get the configured Anthropic LLM instance."""
        if self.llm is None:
            raise RuntimeError("Anthropic LLM not initialized. Please check your configuration.")
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
            # Use complete() instead of chat() for testing to avoid response format issues
            response = self.llm.complete("Hello")
            return bool(response and hasattr(response, 'text') and response.text)
        except Exception as e:
            print(f"Anthropic API connection test failed: {e}")
            return False


# Global instance
anthropic_llm = AnthropicLLM()