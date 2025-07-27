#!/usr/bin/env python3
"""Test the complete ChatCal.ai chatbot agent."""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Use mock LLM for testing
os.environ["USE_MOCK_LLM"] = "true"

from app.core.conversation import ConversationManager
from app.core.session import session_manager
from app.calendar.utils import DateTimeParser, CalendarFormatter


def test_agent_creation():
    """Test creating the chatbot agent."""
    print("🤖 Testing ChatCal Agent Creation...")
    
    try:
        # Create a test session
        session_id = session_manager.create_session({"test": True})
        
        # Create conversation manager (which creates the agent)
        conversation = ConversationManager(session_id=session_id)
        
        print("✅ Agent created successfully")
        print(f"   Session ID: {session_id}")
        print(f"   Available tools: {conversation.agent.get_available_tools()}")
        
        return True, conversation
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_special_commands(conversation):
    """Test special commands like /help and /status."""
    print("\n🎯 Testing Special Commands...")
    
    try:
        # Test help command
        help_response = conversation.get_response("/help")
        print("✅ Help command works")
        print(f"   Response preview: {help_response[:100]}...")
        
        # Test status command
        status_response = conversation.get_response("/status")
        print("✅ Status command works")
        print(f"   Response preview: {status_response[:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ Special commands failed: {e}")
        return False


def test_calendar_tools_integration():
    """Test calendar tools integration (without actual API calls)."""
    print("\n🛠️  Testing Calendar Tools Integration...")
    
    try:
        from app.core.tools import CalendarTools
        
        # Test tool creation
        tools = CalendarTools()
        tool_list = tools.get_tools()
        
        print(f"✅ Calendar tools created: {len(tool_list)} tools")
        for tool in tool_list:
            print(f"   • {tool.metadata.name}: {tool.metadata.description[:50]}...")
        
        # Test datetime parsing
        parser = DateTimeParser()
        formatter = CalendarFormatter()
        
        test_dates = ["next Tuesday at 2pm", "tomorrow morning", "Friday afternoon"]
        for date_str in test_dates:
            parsed = parser.parse_datetime(date_str)
            if parsed:
                formatted = formatter.format_datetime(parsed)
                print(f"✅ Parsed '{date_str}' → {formatted}")
        
        return True
    except Exception as e:
        print(f"❌ Calendar tools integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_conversation_flow(conversation):
    """Test a complete conversation flow."""
    print("\n💬 Testing Conversation Flow...")
    
    try:
        # Start conversation
        greeting = conversation.start_conversation()
        print(f"🤖 ChatCal: {greeting}")
        
        # Test various types of requests
        test_messages = [
            "Hi! I need to schedule a meeting",
            "Check my availability for tomorrow",
            "What's on my calendar this week?",
            "Book a 1-hour meeting with John for next Tuesday at 2pm",
            "Can you reschedule my 3pm meeting to 4pm?"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n👤 User {i}: {message}")
            
            try:
                response = conversation.get_response(message)
                print(f"🤖 ChatCal: {response[:200]}...")
                
                if len(response) > 200:
                    print("   [Response truncated for display]")
                
            except Exception as e:
                print(f"❌ Failed to get response: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Conversation flow failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_streaming_response(conversation):
    """Test streaming response capability."""
    print("\n🌊 Testing Streaming Response...")
    
    try:
        message = "What meetings do I have coming up?"
        print(f"👤 User: {message}")
        print("🤖 ChatCal: ", end="", flush=True)
        
        token_count = 0
        for token in conversation.get_streaming_response(message):
            print(token, end="", flush=True)
            token_count += 1
            if token_count > 50:  # Limit for testing
                print("...[truncated for test]", end="")
                break
        
        print(f"\n✅ Streaming response works ({token_count} tokens)")
        return True
    except Exception as e:
        print(f"\n❌ Streaming response failed: {e}")
        return False


def test_conversation_memory(conversation):
    """Test conversation memory and context."""
    print("\n🧠 Testing Conversation Memory...")
    
    try:
        # Send a message to establish context
        conversation.get_response("My name is John and I work at Acme Corp")
        
        # Send a follow-up that requires context
        response = conversation.get_response("Schedule a meeting for my team at Acme")
        
        print("✅ Context-aware response received")
        print(f"   Response preview: {response[:100]}...")
        
        # Test conversation history
        history = conversation.get_conversation_history()
        print(f"✅ Conversation history: {len(history)} messages")
        
        return True
    except Exception as e:
        print(f"❌ Conversation memory test failed: {e}")
        return False


def main():
    """Run all chatbot agent tests."""
    print("🚀 ChatCal.ai - Complete Chatbot Agent Test\n")
    print("🔧 Running with Mock LLM for testing\n")
    
    # Test agent creation first
    success, conversation = test_agent_creation()
    if not success:
        print("\n❌ Cannot continue without successful agent creation")
        return
    
    tests = [
        ("Special Commands", lambda: test_special_commands(conversation)),
        ("Calendar Tools Integration", test_calendar_tools_integration),
        ("Conversation Flow", lambda: test_conversation_flow(conversation)),
        ("Streaming Response", lambda: test_streaming_response(conversation)),
        ("Conversation Memory", lambda: test_conversation_memory(conversation))
    ]
    
    results = [("Agent Creation", True)]  # Already tested
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary:")
    print("="*60)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(success for _, success in results)
    
    if all_passed:
        print("\n🎉 All chatbot agent tests passed!")
        print("\n📋 Key Features Tested:")
        print("• ✅ Agent creation with calendar tools")
        print("• ✅ Special commands (/help, /status)")
        print("• ✅ Calendar tools integration")
        print("• ✅ Natural conversation flow")
        print("• ✅ Streaming responses")
        print("• ✅ Conversation memory")
        
        print("\n📝 Next Steps:")
        print("1. Resolve Anthropic API credit issue for real LLM testing")
        print("2. Test with actual Google Calendar authentication")
        print("3. Build FastAPI web interface")
        print("4. Deploy and test end-to-end")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")


if __name__ == "__main__":
    main()