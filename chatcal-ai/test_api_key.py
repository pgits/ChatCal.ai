#!/usr/bin/env python3
"""Test Anthropic API key directly."""

import os
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_direct_api():
    """Test API key directly with Anthropic SDK."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    print(f"API Key present: {'Yes' if api_key else 'No'}")
    print(f"API Key length: {len(api_key) if api_key else 0}")
    print(f"API Key prefix: {api_key[:15]}..." if api_key else "No key")
    
    try:
        # Test with direct Anthropic client
        client = Anthropic(api_key=api_key)
        
        # Try a simple completion
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Say 'Hello, I'm working!' in 5 words or less."}
            ]
        )
        
        print(f"\n✅ API call successful!")
        print(f"Response: {response.content[0].text}")
        
    except Exception as e:
        print(f"\n❌ API call failed: {e}")
        print("\nTrying different model names...")
        
        # Try alternative model names
        models_to_try = [
            "claude-sonnet-4-20250514",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-latest", 
            "claude-3-sonnet-20240229",
            "claude-3-5-sonnet"
        ]
        
        for model in models_to_try:
            try:
                print(f"\nTrying model: {model}")
                client = Anthropic(api_key=api_key)
                response = client.messages.create(
                    model=model,
                    max_tokens=50,
                    messages=[{"role": "user", "content": "Hi"}]
                )
                print(f"✅ Success with model: {model}")
                break
            except Exception as e:
                print(f"❌ Failed: {str(e)[:100]}...")

if __name__ == "__main__":
    test_direct_api()