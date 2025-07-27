#!/usr/bin/env python3
"""Basic test script to verify project setup without requiring API calls."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported."""
    print("🔍 Testing module imports...")
    
    try:
        from app.config import settings
        print("✅ Config module imported successfully")
        
        from app.personality.prompts import SYSTEM_PROMPT, GREETING_TEMPLATES
        print("✅ Personality prompts imported successfully")
        
        from llama_index.llms.anthropic import Anthropic
        print("✅ LlamaIndex Anthropic module imported successfully")
        
        import redis
        print("✅ Redis module imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_config():
    """Test configuration loading."""
    print("\n⚙️ Testing configuration...")
    
    try:
        from app.config import settings
        
        # Check required settings are loaded
        assert settings.anthropic_api_key, "Anthropic API key is missing"
        assert settings.google_calendar_id == "pgits.job@gmail.com", "Google Calendar ID mismatch"
        assert settings.app_name == "ChatCal.ai", "App name mismatch"
        
        print("✅ Configuration loaded successfully")
        print(f"   App Name: {settings.app_name}")
        print(f"   Environment: {settings.app_env}")
        print(f"   Calendar ID: {settings.google_calendar_id}")
        print(f"   Redis URL: {settings.redis_url}")
        print(f"   API Key: {'✅ Present' if settings.anthropic_api_key else '❌ Missing'}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_redis_connection():
    """Test Redis connection."""
    print("\n🔗 Testing Redis connection...")
    
    try:
        from app.config import settings
        import redis
        
        client = redis.from_url(settings.redis_url, decode_responses=True)
        
        # Test basic operations
        client.set("test_key", "test_value", ex=5)  # 5 second expiration
        value = client.get("test_key")
        
        if value == "test_value":
            print("✅ Redis connection successful")
            print(f"   Connected to: {settings.redis_url}")
            
            # Cleanup
            client.delete("test_key")
            return True
        else:
            print("❌ Redis test value mismatch")
            return False
            
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("   Make sure Redis is running: redis-server")
        return False


def test_llama_index_setup():
    """Test LlamaIndex setup without API calls."""
    print("\n🦙 Testing LlamaIndex setup...")
    
    try:
        from llama_index.llms.anthropic import Anthropic
        from app.config import settings
        
        # Create LLM instance (without making API calls)
        llm = Anthropic(
            api_key=settings.anthropic_api_key,
            model="claude-3-5-sonnet-20241022",  # Claude 3.5 Sonnet
            max_tokens=100
        )
        
        print("✅ LlamaIndex Anthropic LLM created successfully")
        print(f"   Model: {llm.model}")
        print(f"   Max tokens: {llm.max_tokens}")
        
        return True
    except Exception as e:
        print(f"❌ LlamaIndex setup failed: {e}")
        return False


def test_personality_system():
    """Test personality prompts."""
    print("\n😊 Testing personality system...")
    
    try:
        from app.personality.prompts import (
            SYSTEM_PROMPT, GREETING_TEMPLATES, 
            BOOKING_CONFIRMATIONS, ENCOURAGEMENT_PHRASES
        )
        
        assert len(GREETING_TEMPLATES) > 0, "No greeting templates found"
        assert len(BOOKING_CONFIRMATIONS) > 0, "No booking confirmations found"
        assert len(ENCOURAGEMENT_PHRASES) > 0, "No encouragement phrases found"
        assert "friendly" in SYSTEM_PROMPT.lower(), "System prompt doesn't mention friendly"
        
        print("✅ Personality system loaded successfully")
        print(f"   Greeting templates: {len(GREETING_TEMPLATES)}")
        print(f"   Booking confirmations: {len(BOOKING_CONFIRMATIONS)}")
        print(f"   Encouragement phrases: {len(ENCOURAGEMENT_PHRASES)}")
        print(f"   System prompt length: {len(SYSTEM_PROMPT)} characters")
        
        return True
    except Exception as e:
        print(f"❌ Personality system test failed: {e}")
        return False


def main():
    """Run all basic tests."""
    print("🚀 ChatCal.ai - Basic Setup Test\n")
    
    tests = [
        ("Module Imports", test_imports),
        ("Configuration", test_config),
        ("Redis Connection", test_redis_connection),
        ("LlamaIndex Setup", test_llama_index_setup),
        ("Personality System", test_personality_system)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 Test Summary:")
    print("="*50)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(success for _, success in results)
    if all_passed:
        print("\n🎉 All basic tests passed! The setup is working correctly.")
        print("\n📝 Next steps:")
        print("1. Add credits to your Anthropic account for API testing")
        print("2. Test full conversation flow once credits are available")
        print("3. Proceed with building the Google Calendar integration")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration.")
        
    return all_passed


if __name__ == "__main__":
    main()