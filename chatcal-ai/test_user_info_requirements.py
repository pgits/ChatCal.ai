#!/usr/bin/env python3
"""Test the updated user information requirements."""

import sys
sys.path.append('/Users/petergits/dev/chatCal.ai/chatcal-ai')

from app.core.agent import ChatCalAgent

def test_user_info_requirements():
    """Test that the agent properly tracks required user information."""
    
    # Create a new agent
    agent = ChatCalAgent("test_session")
    
    print("=== Testing User Information Requirements ===\n")
    
    # Test 1: Check initial state (no info collected)
    print("1. Initial state - no information collected:")
    print(f"   Complete info: {agent.has_complete_user_info()}")
    print(f"   Missing info: {agent.get_missing_user_info()}")
    print(f"   User context: {agent._get_user_context()}")
    print()
    
    # Test 2: Add name only
    print("2. After adding name only:")
    agent.update_user_info("name", "John Smith")
    print(f"   Complete info: {agent.has_complete_user_info()}")
    print(f"   Missing info: {agent.get_missing_user_info()}")
    print(f"   User context: {agent._get_user_context()}")
    print()
    
    # Test 3: Add email
    print("3. After adding email:")
    agent.update_user_info("email", "john@example.com")
    print(f"   Complete info: {agent.has_complete_user_info()}")
    print(f"   Missing info: {agent.get_missing_user_info()}")
    print(f"   User context: {agent._get_user_context()}")
    print()
    
    # Test 4: Add phone (complete information)
    print("4. After adding phone (complete):")
    agent.update_user_info("phone", "555-123-4567")
    print(f"   Complete info: {agent.has_complete_user_info()}")
    print(f"   Missing info: {agent.get_missing_user_info()}")
    print(f"   User context: {agent._get_user_context()}")
    print()
    
    # Test 5: Test extraction from message
    print("5. Testing information extraction from message:")
    test_message = "Hi, my name is Sarah Johnson and my email is sarah@example.com. My phone is 555-987-6543."
    extracted = agent.extract_user_info_from_message(test_message)
    print(f"   Extracted info: {extracted}")
    
    return True

if __name__ == "__main__":
    test_user_info_requirements()