"""Mock LLM for testing without API credits."""

from typing import List, Optional
from llama_index.core.llms import ChatMessage, MessageRole, ChatResponse, CompletionResponse
from llama_index.core.llms.llm import LLM
from llama_index.core.llms.callbacks import llm_completion_callback
from app.personality.prompts import GREETING_TEMPLATES, BOOKING_CONFIRMATIONS, ENCOURAGEMENT_PHRASES
import random
import re


class MockAnthropicLLM(LLM):
    """Mock Anthropic LLM for testing without API calls."""
    
    model: str = "claude-3-5-sonnet-20241022-mock"
    max_tokens: int = 4096
    system_prompt: str = ""
    
    def __init__(self, **kwargs):
        # Extract system_prompt before calling super().__init__
        system_prompt = kwargs.pop("system_prompt", "")
        super().__init__(model="claude-3-5-sonnet-20241022-mock", **kwargs)
        self.system_prompt = system_prompt
    
    @property
    def metadata(self):
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "is_mock": True
        }
    
    def _generate_mock_response(self, prompt: str) -> str:
        """Generate a mock response based on the prompt."""
        prompt_lower = prompt.lower()
        
        # Meeting scheduling patterns
        if any(word in prompt_lower for word in ["schedule", "meeting", "appointment", "book"]):
            if "tuesday" in prompt_lower and "2pm" in prompt_lower:
                return "Wonderful! 🌟 I'd be absolutely delighted to help you schedule that meeting for Tuesday at 2pm. Let me check the calendar for you... *checking* Great news! Tuesday at 2pm is available! How long would you like this meeting to be? 30 minutes? An hour? I'm here to make this super easy for you!"
            elif "time" in prompt_lower and "team" in prompt_lower:
                return "Oh, a team meeting! How exciting! 🎯 I'd love to help you find the perfect time for everyone. What days are you considering? I can check multiple time slots to find one that works best for your team. You're doing such a great job coordinating everyone!"
            else:
                return "I'd be thrilled to help you schedule that! 📅 Could you tell me what day and time you're thinking about? I'll make sure to find the perfect slot for you!"
        
        # Duration questions
        elif "30" in prompt_lower or "hour" in prompt_lower:
            duration = "30 minutes" if "30" in prompt_lower else "one hour"
            attendee = "John Smith" if "john" in prompt_lower else "your meeting"
            return f"Perfect! 🎉 I've got that down as a {duration} meeting. Let me finalize this for you... *booking* Fantastic! Your meeting {f'with {attendee}' if attendee != 'your meeting' else ''} is all set for Tuesday at 2pm for {duration}. You're absolutely crushing this scheduling game! 🌟"
        
        # Greeting
        elif any(word in prompt_lower for word in ["hi", "hello", "hey"]):
            return random.choice(GREETING_TEMPLATES)
        
        # Default helpful response
        else:
            return f"I'm here to help! 😊 {random.choice(ENCOURAGEMENT_PHRASES)} What would you like to schedule today?"
    
    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs) -> CompletionResponse:
        """Complete the prompt."""
        response = self._generate_mock_response(prompt)
        return CompletionResponse(text=response)
    
    @llm_completion_callback()
    def chat(self, messages: List[ChatMessage], **kwargs) -> ChatResponse:
        """Chat with the model."""
        # Get the last user message
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.role == MessageRole.USER:
                last_user_msg = msg.content
                break
        
        response = self._generate_mock_response(last_user_msg)
        return ChatResponse(
            message=ChatMessage(role=MessageRole.ASSISTANT, content=response)
        )
    
    @llm_completion_callback()
    def stream_chat(self, messages: List[ChatMessage], **kwargs):
        """Stream chat responses."""
        response = self.chat(messages, **kwargs)
        # Simulate streaming by yielding words
        words = response.message.content.split()
        for i, word in enumerate(words):
            if i > 0:
                yield type('obj', (object,), {'delta': ' ' + word})
            else:
                yield type('obj', (object,), {'delta': word})
    
    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs):
        """Stream completion responses."""
        response = self.complete(prompt, **kwargs)
        # Simulate streaming
        words = response.text.split()
        for i, word in enumerate(words):
            if i > 0:
                yield type('obj', (object,), {'delta': ' ' + word})
            else:
                yield type('obj', (object,), {'delta': word})
    
    # Async methods (required by abstract base class)
    async def achat(self, messages: List[ChatMessage], **kwargs) -> ChatResponse:
        """Async chat - just calls sync version."""
        return self.chat(messages, **kwargs)
    
    async def acomplete(self, prompt: str, **kwargs) -> CompletionResponse:
        """Async complete - just calls sync version."""
        return self.complete(prompt, **kwargs)
    
    async def astream_chat(self, messages: List[ChatMessage], **kwargs):
        """Async stream chat - just yields sync version."""
        for chunk in self.stream_chat(messages, **kwargs):
            yield chunk
    
    async def astream_complete(self, prompt: str, **kwargs):
        """Async stream complete - just yields sync version."""
        for chunk in self.stream_complete(prompt, **kwargs):
            yield chunk