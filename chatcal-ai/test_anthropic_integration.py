#!/usr/bin/env python3
"""Test script to verify Anthropic API integration."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.llm import anthropic_llm
from app.core.conversation import ConversationManager
from app.core.session import session_manager


def test_llm_connection():
    """Test basic LLM connection."""
    print("🔍 Testing Anthropic API connection...")
    
    if anthropic_llm.test_connection():
        print("✅ Anthropic API connection successful!")
        return True
    else:
        print("❌ Anthropic API connection failed!")
        return False


def test_conversation():
    """Test conversation flow."""
    print("\n📝 Testing conversation flow...")
    
    # Create a test session
    session_id = session_manager.create_session({"test": True})
    print(f"✅ Created session: {session_id}")
    
    # Get conversation manager
    conversation = session_manager.get_or_create_conversation(session_id)
    if not conversation:
        print("❌ Failed to create conversation manager!")
        return False
    
    print("✅ Created conversation manager")
    
    # Start conversation
    greeting = conversation.start_conversation()
    print(f"\n🤖 Bot: {greeting}")
    
    # Test user input
    user_message = "Hi! I need to schedule a meeting next Tuesday at 2pm"
    print(f"\n👤 User: {user_message}")
    
    # Get response
    response = conversation.get_response(user_message)
    print(f"\n🤖 Bot: {response}")
    
    # Test follow-up
    follow_up = "It should be a 30-minute meeting with John Smith"
    print(f"\n👤 User: {follow_up}")
    
    response2 = conversation.get_response(follow_up)
    print(f"\n🤖 Bot: {response2}")
    
    # Export conversation
    history = conversation.export_conversation()
    print(f"\n✅ Conversation history: {len(history['messages'])} messages")
    
    return True


def test_streaming():
    """Test streaming responses."""
    print("\n🌊 Testing streaming response...")
    
    session_id = session_manager.create_session()
    conversation = session_manager.get_or_create_conversation(session_id)
    
    if not conversation:
        print("❌ Failed to create conversation for streaming test!")
        return False
    
    user_message = "Can you help me find a good time for a team meeting?"
    print(f"\n👤 User: {user_message}")
    print("\n🤖 Bot: ", end="", flush=True)
    
    # Stream the response
    for token in conversation.get_streaming_response(user_message):
        print(token, end="", flush=True)
    
    print("\n\n✅ Streaming response completed")
    return True


def main():
    """Run all tests."""
    print("🚀 ChatCal.ai - Anthropic Integration Test\n")
    
    tests = [
        ("LLM Connection", test_llm_connection),
        ("Conversation Flow", test_conversation),
        ("Streaming Response", test_streaming)
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
        print("\n🎉 All tests passed! Anthropic integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check your configuration.")
        print("\nMake sure:")
        print("1. Your .env file has valid ANTHROPIC_API_KEY")
        print("2. Redis is running (for session management)")
        print("3. All dependencies are installed")


if __name__ == "__main__":
    main()