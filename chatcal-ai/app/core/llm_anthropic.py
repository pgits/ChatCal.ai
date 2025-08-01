"""Groq LLM integration for ChatCal.ai (using anthropic_llm interface)."""

from typing import Optional
import os
from llama_index.core import Settings
from llama_index.core.llms import ChatMessage, MessageRole
from app.config import settings
from app.personality.prompts import SYSTEM_PROMPT

# Try to import Groq, fall back gracefully if not available
try:
    from llama_index.llms.groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("⚠️ Groq LLM not available - falling back to Anthropic")


class AnthropicLLM:
    """Manages the Groq LLM integration with LlamaIndex (keeping AnthropicLLM name for compatibility)."""
    
    def __init__(self):
        self.api_key = settings.groq_api_key  # Use GROQ_API_KEY instead
        self.llm = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the Groq LLM with LlamaIndex settings."""
        try:
            # Check if we should use mock LLM for testing
            if os.getenv("USE_MOCK_LLM", "").lower() == "true":
                from app.core.mock_llm import MockAnthropicLLM
                self.llm = MockAnthropicLLM(system_prompt=SYSTEM_PROMPT)
                print("🔧 Using Mock LLM for testing")
            elif GROQ_AVAILABLE:
                # Validate API key
                if not self.api_key or self.api_key == "your_groq_api_key_here":
                    raise ValueError("Groq API key not configured. Please set GROQ_API_KEY in .env file")
                
                self.llm = Groq(
                    api_key=self.api_key,
                    model="llama-3.1-8b-instant",  # Using Groq's Llama 3.1 8B Instant
                    max_tokens=4096,
                    temperature=0.7,  # Balanced for friendly conversation
                    system_prompt=SYSTEM_PROMPT
                )
                print("🔧 Using Groq Llama-3.1-8b-instant LLM")
            else:
                # Fallback to Anthropic if Groq not available
                try:
                    from llama_index.llms.anthropic import Anthropic
                    anthropic_api_key = settings.anthropic_api_key
                    if not anthropic_api_key:
                        raise ValueError("Neither Groq nor Anthropic API key configured")
                    
                    self.llm = Anthropic(
                        api_key=anthropic_api_key,
                        model="claude-3-sonnet-20240229",
                        max_tokens=4096,
                        temperature=0.7,
                        system_prompt=SYSTEM_PROMPT
                    )
                    print("🔧 Using Anthropic Claude-3-Sonnet LLM (Groq fallback)")
                except ImportError:
                    # Final fallback to mock LLM
                    from app.core.mock_llm import MockAnthropicLLM
                    self.llm = MockAnthropicLLM(system_prompt=SYSTEM_PROMPT)
                    print("🔧 Using Mock LLM (no providers available)")
            
            # Set as default LLM for LlamaIndex
            Settings.llm = self.llm
            
            # Configure other LlamaIndex settings
            Settings.chunk_size = 1024
            Settings.chunk_overlap = 20
            
        except Exception as e:
            print(f"❌ Failed to initialize LLM: {e}")
            # Fallback to mock LLM if available
            try:
                from app.core.mock_llm import MockAnthropicLLM
                self.llm = MockAnthropicLLM(system_prompt=SYSTEM_PROMPT)
                print("🔧 Falling back to Mock LLM")
            except ImportError:
                raise RuntimeError(f"Failed to initialize LLM and no fallback available: {e}")
    
    def get_llm(self):
        """Get the configured Groq LLM instance."""
        if self.llm is None:
            raise RuntimeError("Groq LLM not initialized. Please check your configuration.")
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
        """Test the connection to Groq API."""
        try:
            # Use complete() instead of chat() for testing to avoid response format issues
            response = self.llm.complete("Hello")
            return bool(response and hasattr(response, 'text') and response.text)
        except Exception as e:
            print(f"Groq API connection test failed: {e}")
            return False


# Global instance
anthropic_llm = AnthropicLLM()