"""Custom exceptions for ChatCal.ai application."""

from typing import Optional, Dict, Any


class ChatCalException(Exception):
    """Base exception for ChatCal.ai application."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(ChatCalException):
    """Raised when authentication fails."""
    pass


class CalendarError(ChatCalException):
    """Raised when calendar operations fail."""
    pass


class LLMError(ChatCalException):
    """Raised when LLM operations fail."""
    pass


class ValidationError(ChatCalException):
    """Raised when input validation fails."""
    pass


class RateLimitError(ChatCalException):
    """Raised when API rate limits are exceeded."""
    pass


class ServiceUnavailableError(ChatCalException):
    """Raised when external services are unavailable."""
    pass


class ConfigurationError(ChatCalException):
    """Raised when configuration is invalid."""
    pass