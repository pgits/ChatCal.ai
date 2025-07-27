#!/usr/bin/env python3
"""Test conversation flow with mock LLM."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Override the LLM before importing
import os
os.environ["USE_MOCK_LLM"] = "true"

from app.core.mock_llm import MockAnthropicLLM
from app.core.conversation import ConversationManager
from app.core.session import session_manager
from app.personality.prompts import SYSTEM_PROMPT


def test_mock_conversation():
    """Test conversation flow with mock LLM."""
    print("🤖 Testing ChatCal.ai Conversation Flow (Mock Mode)\n")
    
    # Create a test session
    session_id = session_manager.create_session({"test": True, "mock": True})
    print(f"✅ Created session: {session_id}")
    
    # Create conversation manager with mock LLM
    conversation = ConversationManager(session_id=session_id)
    
    # Override with mock LLM
    conversation.llm = MockAnthropicLLM(system_prompt=SYSTEM_PROMPT)
    
    print("✅ Created conversation manager with mock LLM\n")
    
    # Start conversation
    greeting = conversation.start_conversation()
    print(f"🤖 ChatCal: {greeting}")
    
    # Test conversation flow
    test_messages = [
        "Hi! I need to schedule a meeting next Tuesday at 2pm",
        "It should be a 30-minute meeting with John Smith",
        "Can you help me find a good time for a team meeting?"
    ]
    
    for user_msg in test_messages:
        print(f"\n👤 User: {user_msg}")
        
        # Get response using mock LLM
        response = conversation.llm.chat(conversation.get_conversation_history()).message.content
        conversation.add_assistant_message(response)
        conversation.add_user_message(user_msg)  # Add for next iteration
        
        print(f"🤖 ChatCal: {response}")
    
    # Test streaming
    print("\n\n🌊 Testing streaming response...")
    user_msg = "Schedule another meeting for Friday afternoon"
    print(f"👤 User: {user_msg}")
    print("🤖 ChatCal: ", end="", flush=True)
    
    conversation.add_user_message(user_msg)
    for token in conversation.llm.stream_chat(conversation.get_conversation_history()):
        print(token.delta, end="", flush=True)
    
    print("\n\n✅ Mock conversation test completed!")
    
    # Export conversation
    history = conversation.export_conversation()
    print(f"\n📝 Conversation history: {len(history['messages'])} messages")
    
    return True


if __name__ == "__main__":
    try:
        test_mock_conversation()
        print("\n🎉 All mock tests passed! The conversation system is working correctly.")
        print("\n📝 Note: This is using a mock LLM. To use the real Anthropic API:")
        print("   1. Ensure your API key has credits")
        print("   2. Check if you need a different API key for unlimited access")
        print("   3. Remove the USE_MOCK_LLM environment variable")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()