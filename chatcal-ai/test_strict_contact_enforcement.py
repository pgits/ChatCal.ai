#!/usr/bin/env python3
"""Test the strict contact information enforcement."""

import sys
sys.path.append('/Users/petergits/dev/chatCal.ai/chatcal-ai')

from app.core.agent import ChatCalAgent
from app.config import settings

def test_strict_enforcement():
    """Test that the agent strictly enforces contact collection before booking."""
    
    print("=== Testing Strict Contact Information Enforcement ===\n")
    
    # Test 1: Check Peter's contact info is loaded
    print("1. Peter's contact information from settings:")
    print(f"   Phone: {settings.my_phone_number}")
    print(f"   Email: {settings.my_email_address}")
    print()
    
    # Test 2: Check initial strict messaging
    print("2. Initial state - strict no-booking enforcement:")
    agent = ChatCalAgent("test_strict_session")
    context = agent._get_user_context()
    print(f"   Context includes Peter's phone: {'my_phone_number' in context or settings.my_phone_number in context}")
    print(f"   Context includes booking prohibition: {'DO NOT USE create_appointment' in context}")
    print(f"   Context snippet: {context[:200]}...")
    print()
    
    # Test 3: Name only - should still prohibit booking
    print("3. After adding name only - should still prohibit:")
    agent.update_user_info("name", "John Smith")
    context = agent._get_user_context()
    print(f"   Can book: {agent.has_complete_user_info()}")
    print(f"   Context prohibits booking: {'FORBIDDEN' in context or 'DO NOT' in context}")
    print(f"   Missing contact warning: {'CONTACT' in context}")
    print()
    
    # Test 4: Name + email - should allow booking
    print("4. After adding email - should allow booking:")
    agent.update_user_info("email", "john@example.com")
    context = agent._get_user_context()
    print(f"   Can book: {agent.has_complete_user_info()}")
    print(f"   Context allows booking: {'Ready to book' in context}")
    print(f"   Context snippet: {context[-200:]}")
    print()
    
    return True

if __name__ == "__main__":
    test_strict_enforcement()