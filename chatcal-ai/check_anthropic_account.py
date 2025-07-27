#!/usr/bin/env python3
"""Check Anthropic account details."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def check_account():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    print("🔍 Checking Anthropic Account Details\n")
    print(f"API Key: {api_key[:20]}...{api_key[-10:]}")
    print(f"API Key Length: {len(api_key)}")
    print(f"API Key Format: {'Valid' if api_key.startswith('sk-ant-api') else 'Invalid'}")
    
    # Try a basic API call with proper headers
    headers = {
        "x-api-key": api_key,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    # Test with minimal request
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "Hi"}]
    }
    
    print("\n📡 Testing API endpoint directly...")
    
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("\n✅ API is working!")
        else:
            print("\n❌ API request failed")
            
            # Check if it's a different error
            if "credit" in response.text.lower():
                print("\n💡 This appears to be a credit/billing issue.")
                print("   Please check:")
                print("   1. Log into console.anthropic.com")
                print("   2. Navigate to Plans & Billing")
                print("   3. Verify your credit balance or plan status")
                print("   4. Make sure this API key is from the correct workspace")
            
    except Exception as e:
        print(f"\n❌ Request failed: {e}")

if __name__ == "__main__":
    check_account()