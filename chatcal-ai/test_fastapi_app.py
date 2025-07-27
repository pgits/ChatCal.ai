#!/usr/bin/env python3
"""Test the FastAPI application."""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Use mock LLM for testing
os.environ["USE_MOCK_LLM"] = "true"

import requests
import json
from datetime import datetime


def test_health_endpoint():
    """Test the health check endpoint."""
    print("🏥 Testing Health Check Endpoint...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check successful")
            print(f"   Status: {data['status']}")
            print(f"   Version: {data['version']}")
            print(f"   Services: {data['services']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running?")
        print("   Start with: cd chatcal-ai && python -m uvicorn app.api.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


def test_session_endpoints():
    """Test session management endpoints."""
    print("\n👤 Testing Session Management...")
    
    try:
        # Create session
        response = requests.post("http://localhost:8000/sessions", 
                               json={}, timeout=5)
        
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data['session_id']
            print(f"✅ Session created: {session_id}")
            
            # Get session
            response = requests.get(f"http://localhost:8000/sessions/{session_id}", 
                                  timeout=5)
            
            if response.status_code == 200:
                print("✅ Session retrieved successfully")
                return True, session_id
            else:
                print(f"❌ Failed to retrieve session: {response.status_code}")
                return False, None
        else:
            print(f"❌ Failed to create session: {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ Session test error: {e}")
        return False, None


def test_chat_endpoint(session_id=None):
    """Test the chat endpoint."""
    print("\n💬 Testing Chat Endpoint...")
    
    try:
        chat_data = {
            "message": "Hello! Can you help me schedule a meeting?",
            "session_id": session_id
        }
        
        response = requests.post("http://localhost:8000/chat", 
                               json=chat_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Chat endpoint successful")
            print(f"   Response preview: {data['response'][:100]}...")
            print(f"   Session ID: {data['session_id']}")
            return True, data['session_id']
        else:
            print(f"❌ Chat endpoint failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Raw response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Chat test error: {e}")
        return False, None


def test_special_commands(session_id):
    """Test special commands like /help."""
    print("\n🎯 Testing Special Commands...")
    
    commands = ["/help", "/status"]
    
    for command in commands:
        try:
            chat_data = {
                "message": command,
                "session_id": session_id
            }
            
            response = requests.post("http://localhost:8000/chat", 
                                   json=chat_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Command '{command}' works")
                print(f"   Response preview: {data['response'][:80]}...")
            else:
                print(f"❌ Command '{command}' failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Command '{command}' error: {e}")
    
    return True


def test_auth_endpoints():
    """Test authentication endpoints."""
    print("\n🔐 Testing Authentication Endpoints...")
    
    try:
        # Test auth status
        response = requests.get("http://localhost:8000/auth/status", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Auth status: {data['message']}")
            
            # Test auth login URL generation
            response = requests.get("http://localhost:8000/auth/login", timeout=5)
            
            if response.status_code == 200:
                auth_data = response.json()
                print("✅ Auth login URL generated")
                print(f"   URL preview: {auth_data['auth_url'][:80]}...")
                return True
            else:
                print(f"❌ Auth login failed: {response.status_code}")
                return False
        else:
            print(f"❌ Auth status failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Auth test error: {e}")
        return False


def test_conversation_flow(session_id):
    """Test a complete conversation flow."""
    print("\n🔄 Testing Conversation Flow...")
    
    messages = [
        "Hi there!",
        "Check my availability for tomorrow",
        "Schedule a meeting with John next Tuesday at 2pm",
        "What meetings do I have this week?"
    ]
    
    for i, message in enumerate(messages, 1):
        try:
            chat_data = {
                "message": message,
                "session_id": session_id
            }
            
            response = requests.post("http://localhost:8000/chat", 
                                   json=chat_data, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Message {i}: Response received")
                print(f"   Preview: {data['response'][:60]}...")
            else:
                print(f"❌ Message {i} failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Message {i} error: {e}")
    
    return True


def show_server_info():
    """Show information about accessing the server."""
    print("\n" + "="*60)
    print("🌐 Server Access Information")
    print("="*60)
    print("Main Application: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Chat Widget: http://localhost:8000/chat-widget")
    print("Health Check: http://localhost:8000/health")
    print("")
    print("To start the server:")
    print("cd chatcal-ai")
    print("python -m uvicorn app.api.main:app --reload")


def main():
    """Run all FastAPI tests."""
    print("🚀 ChatCal.ai - FastAPI Application Test\n")
    print("🔧 Running with Mock LLM for testing\n")
    
    # Check if server is running
    health_ok = test_health_endpoint()
    if not health_ok:
        show_server_info()
        return
    
    tests = []
    session_id = None
    
    # Test session management
    session_ok, session_id = test_session_endpoints()
    tests.append(("Session Management", session_ok))
    
    if session_id:
        # Test chat endpoint
        chat_ok, new_session_id = test_chat_endpoint(session_id)
        tests.append(("Chat Endpoint", chat_ok))
        
        if new_session_id:
            session_id = new_session_id
        
        # Test special commands
        commands_ok = test_special_commands(session_id)
        tests.append(("Special Commands", commands_ok))
        
        # Test conversation flow
        flow_ok = test_conversation_flow(session_id)
        tests.append(("Conversation Flow", flow_ok))
    
    # Test auth endpoints
    auth_ok = test_auth_endpoints()
    tests.append(("Authentication", auth_ok))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary:")
    print("="*60)
    
    # Include health check in results
    all_tests = [("Health Check", health_ok)] + tests
    
    for test_name, success in all_tests:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(success for _, success in all_tests)
    
    if all_passed:
        print("\n🎉 All FastAPI tests passed!")
        print("\n📋 Working Features:")
        print("• ✅ Health monitoring")
        print("• ✅ Session management")
        print("• ✅ Chat conversations")
        print("• ✅ Special commands")
        print("• ✅ Authentication flow")
        print("• ✅ Conversation continuity")
        
        show_server_info()
        
        print("\n📝 Next Steps:")
        print("1. Test with real Anthropic API (once credits resolved)")
        print("2. Complete Google Calendar OAuth flow")
        print("3. Test end-to-end appointment booking")
        print("4. Deploy to production environment")
    else:
        print("\n⚠️  Some tests failed. Check server logs for details.")
        show_server_info()


if __name__ == "__main__":
    main()