#!/usr/bin/env python3
"""Test the updated user information requirements."""

import sys
sys.path.append('/Users/petergits/dev/chatCal.ai/chatcal-ai')

from app.core.agent import ChatCalAgent

def test_user_info_requirements():
    """Test that the agent properly tracks required user information."""
    
    print("=== Testing Flexible User Information Requirements ===\n")
    
    # Test 1: Check initial state (no info collected)
    print("1. Initial state - no information collected:")
    agent1 = ChatCalAgent("test_session_1")
    print(f"   Required info complete: {agent1.has_complete_user_info()}")
    print(f"   Ideal info complete: {agent1.has_ideal_user_info()}")
    print(f"   Missing required: {agent1.get_missing_user_info()}")
    print(f"   User context: {agent1._get_user_context()}")
    print()
    
    # Test 2: Add name only
    print("2. After adding name only:")
    agent1.update_user_info("name", "John Smith")
    print(f"   Required info complete: {agent1.has_complete_user_info()}")
    print(f"   Missing required: {agent1.get_missing_user_info()}")
    print(f"   User context: {agent1._get_user_context()}")
    print()
    
    # Test 3: Add email (should be sufficient with name)
    print("3. After adding email (name + email = sufficient):")
    agent1.update_user_info("email", "john@example.com")
    print(f"   Required info complete: {agent1.has_complete_user_info()}")
    print(f"   Ideal info complete: {agent1.has_ideal_user_info()}")
    print(f"   Missing required: {agent1.get_missing_user_info()}")
    print(f"   Missing ideal: {agent1.get_missing_ideal_info()}")
    print(f"   User context: {agent1._get_user_context()}")
    print()
    
    # Test 4: Alternative path - name + phone only
    print("4. Alternative: Name + phone only (no email):")
    agent2 = ChatCalAgent("test_session_2")
    agent2.update_user_info("name", "Jane Doe")
    agent2.update_user_info("phone", "555-987-6543")
    print(f"   Required info complete: {agent2.has_complete_user_info()}")
    print(f"   Ideal info complete: {agent2.has_ideal_user_info()}")
    print(f"   Missing required: {agent2.get_missing_user_info()}")
    print(f"   User context: {agent2._get_user_context()}")
    print()
    
    # Test 5: Add phone to first agent (ideal complete info)
    print("5. Adding phone to first agent (ideal complete):")
    agent1.update_user_info("phone", "555-123-4567")
    print(f"   Required info complete: {agent1.has_complete_user_info()}")
    print(f"   Ideal info complete: {agent1.has_ideal_user_info()}")
    print(f"   User context: {agent1._get_user_context()}")
    print()
    
    return True

if __name__ == "__main__":
    test_user_info_requirements()