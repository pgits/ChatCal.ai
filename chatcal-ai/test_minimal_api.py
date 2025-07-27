#!/usr/bin/env python3
"""Test with minimal API usage."""

import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

def test_minimal():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    print(f"Testing with API key: {api_key[:20]}...")
    
    # Try with absolute minimum tokens
    client = Anthropic(api_key=api_key)
    
    try:
        # Try the most basic request possible
        response = client.messages.create(
            model="claude-3-haiku-20240307",  # Cheapest model
            max_tokens=1,  # Minimum tokens
            messages=[{"role": "user", "content": "Hi"}]
        )
        print("✅ Success! API is working.")
        print(f"Response: {response.content[0].text}")
        
    except Exception as e:
        print(f"❌ Failed with Haiku: {e}")
        
        # Try with instant model
        try:
            response = client.messages.create(
                model="claude-instant-1.2",
                max_tokens=1,
                messages=[{"role": "user", "content": "Hi"}]
            )
            print("✅ Success with Claude Instant!")
            
        except Exception as e2:
            print(f"❌ Failed with Instant: {e2}")
            
            # Check headers
            print("\nAPI Key details:")
            print(f"- Length: {len(api_key)}")
            print(f"- Starts with: {api_key[:15]}")
            print(f"- Format looks valid: {api_key.startswith('sk-ant-api')}")

if __name__ == "__main__":
    test_minimal()