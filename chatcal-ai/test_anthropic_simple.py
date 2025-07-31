#!/usr/bin/env python3
"""Simple test to verify the Anthropic LLM integration is working."""

import os
import sys
sys.path.append('/Users/petergits/dev/chatCal.ai/chatcal-ai')

from app.core.llm_anthropic import anthropic_llm

def test_anthropic_integration():
    """Test that we can initialize and use the Anthropic LLM."""
    try:
        # Test initialization
        print("Testing Anthropic LLM initialization...")
        llm = anthropic_llm.get_llm()
        print(f"✅ LLM initialized successfully: {type(llm)}")
        
        # Test connection
        print("Testing Anthropic connection...")
        is_connected = anthropic_llm.test_connection()
        print(f"✅ Connection test: {'PASSED' if is_connected else 'FAILED'}")
        
        # Test basic completion
        print("Testing basic completion...")
        response = llm.complete("Hello, can you respond with just 'Hi there!'?")
        print(f"✅ Response received: {response.text[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Anthropic integration: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Anthropic Integration ===")
    success = test_anthropic_integration()
    print(f"\n=== Test {'PASSED' if success else 'FAILED'} ===")