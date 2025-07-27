"""Tests for Gemini LLM integration."""

import pytest
from unittest.mock import Mock, patch
from app.core.llm_gemini import GeminiLLM


class TestGeminiLLM:
    """Test cases for GeminiLLM."""
    
    @patch('app.core.llm_gemini.settings')
    def test_initialization_with_valid_key(self, mock_settings):
        """Test LLM initialization with valid API key."""
        mock_settings.gemini_api_key = "valid-api-key"
        
        with patch('app.core.llm_gemini.Gemini') as mock_gemini:
            llm = GeminiLLM()
            assert llm.api_key == "valid-api-key"
            mock_gemini.assert_called_once()
    
    @patch('app.core.llm_gemini.settings')
    def test_initialization_with_invalid_key(self, mock_settings):
        """Test LLM initialization with invalid API key."""
        mock_settings.gemini_api_key = "your_gemini_api_key_here"
        
        with pytest.raises(ValueError, match="Gemini API key not configured"):
            GeminiLLM()
    
    @patch('app.core.llm_gemini.settings')
    @patch('app.core.llm_gemini.os.getenv')
    def test_mock_llm_initialization(self, mock_getenv, mock_settings):
        """Test initialization with mock LLM."""
        mock_settings.gemini_api_key = "valid-api-key"
        mock_getenv.return_value = "true"
        
        with patch('app.core.llm_gemini.MockAnthropicLLM') as mock_llm:
            llm = GeminiLLM()
            mock_llm.assert_called_once()
    
    @patch('app.core.llm_gemini.settings')
    def test_get_llm_success(self, mock_settings):
        """Test successful LLM retrieval."""
        mock_settings.gemini_api_key = "valid-api-key"
        
        with patch('app.core.llm_gemini.Gemini') as mock_gemini:
            mock_instance = Mock()
            mock_gemini.return_value = mock_instance
            
            llm = GeminiLLM()
            result = llm.get_llm()
            assert result == mock_instance
    
    @patch('app.core.llm_gemini.settings')
    def test_get_llm_not_initialized(self, mock_settings):
        """Test LLM retrieval when not initialized."""
        mock_settings.gemini_api_key = "valid-api-key"
        
        with patch('app.core.llm_gemini.Gemini') as mock_gemini:
            mock_gemini.side_effect = Exception("Initialization failed")
            
            with pytest.raises(RuntimeError, match="Failed to initialize Gemini LLM"):
                GeminiLLM()
    
    @patch('app.core.llm_gemini.settings')
    def test_test_connection_success(self, mock_settings):
        """Test successful connection test."""
        mock_settings.gemini_api_key = "valid-api-key"
        
        with patch('app.core.llm_gemini.Gemini') as mock_gemini:
            mock_instance = Mock()
            mock_response = Mock()
            mock_response.text = "Hello"
            mock_instance.complete.return_value = mock_response
            mock_gemini.return_value = mock_instance
            
            llm = GeminiLLM()
            result = llm.test_connection()
            assert result is True
    
    @patch('app.core.llm_gemini.settings')
    def test_test_connection_failure(self, mock_settings):
        """Test failed connection test."""
        mock_settings.gemini_api_key = "valid-api-key"
        
        with patch('app.core.llm_gemini.Gemini') as mock_gemini:
            mock_instance = Mock()
            mock_instance.complete.side_effect = Exception("API Error")
            mock_gemini.return_value = mock_instance
            
            llm = GeminiLLM()
            result = llm.test_connection()
            assert result is False