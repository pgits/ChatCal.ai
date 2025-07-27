"""Input validation utilities for ChatCal.ai."""

import re
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from app.core.exceptions import ValidationError


class InputValidator:
    """Validates user inputs for the chat application."""
    
    # Email validation regex
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    # Time patterns for natural language
    TIME_PATTERNS = [
        r'\d{1,2}:\d{2}\s*(am|pm|AM|PM)?',
        r'\d{1,2}\s*(am|pm|AM|PM)',
        r'(morning|afternoon|evening|noon)',
        r'(early|late)\s+(morning|afternoon|evening)'
    ]
    
    @staticmethod
    def validate_message(message: str) -> str:
        """Validate chat message input."""
        if not message:
            raise ValidationError("Message cannot be empty")
        
        message = message.strip()
        if not message:
            raise ValidationError("Message cannot be empty")
        
        if len(message) > 1000:
            raise ValidationError("Message too long (max 1000 characters)")
        
        # Check for potential injection attempts
        suspicious_patterns = [
            r'<script.*?>',
            r'javascript:',
            r'on\w+\s*=',
            r'eval\s*\(',
            r'exec\s*\('
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                raise ValidationError("Message contains potentially harmful content")
        
        return message
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email address."""
        if not email:
            raise ValidationError("Email cannot be empty")
        
        email = email.strip().lower()
        if not InputValidator.EMAIL_PATTERN.match(email):
            raise ValidationError("Invalid email format")
        
        if len(email) > 254:  # RFC 5321 limit
            raise ValidationError("Email address too long")
        
        return email
    
    @staticmethod
    def validate_email_list(emails: List[str]) -> List[str]:
        """Validate a list of email addresses."""
        if not emails:
            return []
        
        if len(emails) > 50:  # Reasonable limit
            raise ValidationError("Too many attendees (max 50)")
        
        validated_emails = []
        for email in emails:
            validated_emails.append(InputValidator.validate_email(email))
        
        return validated_emails
    
    @staticmethod
    def validate_session_id(session_id: str) -> str:
        """Validate session ID format."""
        if not session_id:
            raise ValidationError("Session ID cannot be empty")
        
        session_id = session_id.strip()
        
        # Check for valid UUID-like format or similar
        if not re.match(r'^[a-zA-Z0-9\-_]{8,64}$', session_id):
            raise ValidationError("Invalid session ID format")
        
        return session_id
    
    @staticmethod
    def validate_duration(duration_minutes: int) -> int:
        """Validate meeting duration."""
        if duration_minutes < 15:
            raise ValidationError("Meeting duration must be at least 15 minutes")
        
        if duration_minutes > 480:  # 8 hours
            raise ValidationError("Meeting duration cannot exceed 8 hours")
        
        # Return as-is for exact durations, round others to nearest 15 minutes
        if duration_minutes % 15 == 0:
            return duration_minutes
        return ((duration_minutes + 7) // 15) * 15
    
    @staticmethod
    def validate_title(title: str) -> str:
        """Validate meeting title."""
        if not title:
            raise ValidationError("Meeting title cannot be empty")
        
        title = title.strip()
        if not title:
            raise ValidationError("Meeting title cannot be empty")
        
        if len(title) > 200:
            raise ValidationError("Meeting title too long (max 200 characters)")
        
        return title
    
    @staticmethod
    def validate_description(description: Optional[str]) -> Optional[str]:
        """Validate meeting description."""
        if not description:
            return None
        
        description = description.strip()
        if not description:
            return None
        
        if len(description) > 1000:
            raise ValidationError("Meeting description too long (max 1000 characters)")
        
        return description
    
    @staticmethod
    def sanitize_user_input(text: str) -> str:
        """Sanitize user input for safe processing."""
        if not text:
            return ""
        
        # Remove potentially harmful characters
        text = re.sub(r'[<>&"\'`]', '', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    @staticmethod
    def validate_time_range(start_time: datetime, end_time: datetime) -> Tuple[datetime, datetime]:
        """Validate time range for calendar events."""
        if start_time >= end_time:
            raise ValidationError("Start time must be before end time")
        
        # Check if event is too far in the future (2 years)
        max_future = datetime.now() + timedelta(days=730)
        if start_time > max_future:
            raise ValidationError("Cannot schedule events more than 2 years in advance")
        
        # Check if event is in the past (with 5 minute buffer)
        min_time = datetime.now() - timedelta(minutes=5)
        if start_time < min_time:
            raise ValidationError("Cannot schedule events in the past")
        
        # Check maximum event duration (24 hours)
        if end_time - start_time > timedelta(hours=24):
            raise ValidationError("Event duration cannot exceed 24 hours")
        
        return start_time, end_time