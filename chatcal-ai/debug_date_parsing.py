#!/usr/bin/env python3
"""Debug script to test date parsing directly."""

import re

def debug_extract_date(message_lower: str) -> str:
    """Extract date from message with detailed debugging."""
    print(f"🔍 DEBUG: Extracting date from message: '{message_lower}'")
    
    date_patterns = [
        (r"tomorrow", "tomorrow"),
        (r"today", "today"),
        (r"monday|tuesday|wednesday|thursday|friday|saturday|sunday", None),
        (r"next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", None),
        (r"this\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", None),
        (r"\d{1,2}/\d{1,2}/\d{2,4}", None),
        (r"\d{1,2}/\d{1,2}", None),
        (r"next week", "next week"),
        (r"this week", "this week")
    ]
    
    for i, (pattern, default_value) in enumerate(date_patterns):
        print(f"🔍 DEBUG: Testing pattern {i+1}: '{pattern}'")
        match = re.search(pattern, message_lower)
        if match:
            result = default_value or match.group()
            print(f"🔍 DEBUG: ✅ Pattern '{pattern}' matched '{match.group()}', returning '{result}'")
            return result
        else:
            print(f"🔍 DEBUG: ❌ Pattern '{pattern}' did not match")
    
    print(f"🔍 DEBUG: No date pattern matched, returning None")
    return None

if __name__ == "__main__":
    # Test cases
    test_messages = [
        "book tomorrow at 3pm for 30 minutes",
        "schedule for tomorrow",
        "I want to meet tomorrow",
        "available tomorrow afternoon",
        "today at 2pm",
        "next monday at 10am",
        "friday meeting"
    ]
    
    print("=== Date Parsing Debug Test ===")
    for msg in test_messages:
        print(f"\n📝 Testing: '{msg}'")
        result = debug_extract_date(msg.lower())
        print(f"🎯 Result: {repr(result)}")
        print("---")