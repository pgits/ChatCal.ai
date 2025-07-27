"""Tests for input validation."""

import pytest
from datetime import datetime, timedelta
from app.core.validators import InputValidator
from app.core.exceptions import ValidationError


class TestInputValidator:
    """Test cases for InputValidator."""
    
    def test_validate_message_valid(self):
        """Test valid message validation."""
        message = "Schedule a meeting with John"
        result = InputValidator.validate_message(message)
        assert result == message
    
    def test_validate_message_empty(self):
        """Test empty message validation."""
        with pytest.raises(ValidationError, match="Message cannot be empty"):
            InputValidator.validate_message("")
        
        with pytest.raises(ValidationError, match="Message cannot be empty"):
            InputValidator.validate_message("   ")
    
    def test_validate_message_too_long(self):
        """Test message too long validation."""
        long_message = "a" * 1001
        with pytest.raises(ValidationError, match="Message too long"):
            InputValidator.validate_message(long_message)
    
    def test_validate_email_valid(self):
        """Test valid email validation."""
        email = "test@example.com"
        result = InputValidator.validate_email(email)
        assert result == email.lower()
    
    def test_validate_email_invalid(self):
        """Test invalid email validation."""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test.example.com",
            ""
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValidationError):
                InputValidator.validate_email(email)
    
    def test_validate_duration_valid(self):
        """Test valid duration validation."""
        result = InputValidator.validate_duration(60)
        assert result == 60
        
        # Test rounding to nearest 15 minutes (67 rounds down to 60)
        result = InputValidator.validate_duration(67)
        assert result == 60
        
        # Test rounding up (68 rounds up to 75)
        result = InputValidator.validate_duration(68)
        assert result == 75
    
    def test_validate_duration_invalid(self):
        """Test invalid duration validation."""
        with pytest.raises(ValidationError, match="at least 15 minutes"):
            InputValidator.validate_duration(10)
        
        with pytest.raises(ValidationError, match="cannot exceed 8 hours"):
            InputValidator.validate_duration(500)
    
    def test_validate_title_valid(self):
        """Test valid title validation."""
        title = "Team Meeting"
        result = InputValidator.validate_title(title)
        assert result == title
    
    def test_validate_title_invalid(self):
        """Test invalid title validation."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            InputValidator.validate_title("")
        
        long_title = "a" * 201
        with pytest.raises(ValidationError, match="too long"):
            InputValidator.validate_title(long_title)
    
    def test_validate_time_range_valid(self):
        """Test valid time range validation."""
        start = datetime.now() + timedelta(hours=1)
        end = start + timedelta(hours=1)
        
        result_start, result_end = InputValidator.validate_time_range(start, end)
        assert result_start == start
        assert result_end == end
    
    def test_validate_time_range_invalid(self):
        """Test invalid time range validation."""
        start = datetime.now() + timedelta(hours=2)
        end = datetime.now() + timedelta(hours=1)
        
        with pytest.raises(ValidationError, match="Start time must be before end time"):
            InputValidator.validate_time_range(start, end)
    
    def test_sanitize_user_input(self):
        """Test user input sanitization."""
        malicious_input = "<script>alert('xss')</script>Hello World"
        result = InputValidator.sanitize_user_input(malicious_input)
        assert "<script>" not in result
        assert "Hello World" in result