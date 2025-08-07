#!/usr/bin/env python3
"""Test phone number extraction from user messages."""

import re

def test_phone_extraction():
    """Test phone number extraction patterns."""
    
    phone_patterns = [
        r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',  # Standard format
        r'call me at\s*(\d{3})[-.\s]*(\d{3})[-.\s]*(\d{4})',  # "call me at" format
        r'phone\s*:?\s*(\d{3})[-.\s]*(\d{3})[-.\s]*(\d{4})',  # "phone:" format
        r'(\d{3})[-.\s]+(\d{3})[-.\s]+(\d{4})',  # Simple space/dash separated
        r'my number is\s*(\d{3})[-.\s]*(\d{3})[-.\s]*(\d{4})',  # "my number is" format
        r'number is\s*(\d{3})[-.\s]*(\d{3})[-.\s]*(\d{4})',  # "number is" format
    ]
    
    test_messages = [
        "Book a meeting with Pete tomorrow at 10:00 AM for 15 minutes, my name is AliceNotTooEarly, make it a phone call, my number is 630 880 5488",
        "Call me at 630 880 5488",
        "My phone number is 6308805488",
        "You can reach me at (630) 880-5488",
        "Phone: 630-880-5488",
        "My number is 630 880 5488"
    ]
    
    print("🧪 Testing Phone Number Extraction")
    print("=" * 50)
    
    for message in test_messages:
        print(f"\nMessage: '{message}'")
        extracted = {}
        
        for i, pattern in enumerate(phone_patterns):
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                match = matches[0]
                print(f"  Pattern {i+1}: {pattern}")
                print(f"  Match: {match}")
                
                if isinstance(match, tuple):
                    # Join all non-empty parts
                    phone_digits = ''.join([part for part in match if part])
                    if len(phone_digits) >= 10:  # Valid phone number
                        extracted['phone'] = phone_digits
                        print(f"  ✅ Extracted: {phone_digits}")
                        break
                    else:
                        print(f"  ❌ Too short: {phone_digits}")
                else:
                    extracted['phone'] = match
                    print(f"  ✅ Extracted: {match}")
                    break
        
        if not extracted.get('phone'):
            print("  ❌ No phone number extracted")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_phone_extraction()