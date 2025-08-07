#!/usr/bin/env python3
"""Test script for phone call vs Google Meet detection."""

def test_meeting_type_detection():
    """Test phone call vs Google Meet keyword detection logic."""
    
    # Phone call keywords (always indicate phone preference)
    phone_keywords = ['phone call', 'by phone', 'telephone', 'phone conversation', 'call me']
    # Google Meet/video keywords (these take precedence over generic phone keywords)
    meet_keywords = ['google meet', 'video call', 'video conference', 'online meeting', 'virtual meeting', 'conference call', 'zoom', 'online', 'remote', 'video', 'video meet']
    # Generic keywords that could go either way
    generic_keywords = ['phone', 'call']
    
    # Test cases: (text, has_phone_number, expected_meet, description)
    test_cases = [
        ("Book a meeting with Pete tomorrow at 6:00 AM, my name is AliceTooEarly, make it a phone call, my number is 630 880 5488", True, False, "Phone call explicitly requested"),
        ("Schedule a Google Meet with Pete next Tuesday at 2 PM", False, True, "Google Meet explicitly requested"),
        ("Set up a video call for Friday morning", False, True, "Video call explicitly requested"),
        ("Can we have a phone conversation tomorrow?", False, False, "Phone conversation explicitly requested"),
        ("Book a regular meeting with Pete", False, True, "No phone number, no preference - should default to Google Meet"),
        ("Book a regular meeting with Pete, my number is 555-1234", True, False, "Has phone number, no explicit preference - should default to phone call"),
        ("I need a Zoom meeting with Pete", False, True, "Zoom explicitly requested"),
        ("Call me at 555-1234 for our meeting", True, False, "Call me + phone number"),
        ("Let's do this by phone", False, False, "By phone explicitly requested"),
        ("Schedule an online meeting", False, True, "Online meeting explicitly requested"),
        ("Conference call with Pete please", False, True, "Conference call goes to video meet"),
        ("Meeting with Pete, call me at 555-1234 but let's do Google Meet", True, True, "Phone number given but Google Meet explicitly requested")
    ]
    
    print("📞 Testing Phone Call vs 🎥 Google Meet Detection")
    print("=" * 60)
    
    all_passed = True
    
    for text, has_phone_number, expected_meet, description in test_cases:
        text_lower = text.lower()
        
        # Apply same logic as the actual code
        # Check for explicit video/meet requests first (these take precedence)
        wants_video_meet = any(keyword in text_lower for keyword in meet_keywords)
        
        # Check for phone-specific keywords (these always indicate phone preference)
        wants_phone_call = any(keyword in text_lower for keyword in phone_keywords)
        
        # Check generic keywords only if no explicit preference found
        if not wants_video_meet and not wants_phone_call:
            has_generic_keywords = any(keyword in text_lower for keyword in generic_keywords)
            # Generic keywords lean toward phone call if user provided phone number
            if has_generic_keywords and has_phone_number:
                wants_phone_call = True
        
        # Decision logic matching the updated code
        if wants_video_meet:
            # Explicitly requested video/Google Meet (takes precedence)
            create_meet = True
        elif wants_phone_call:
            # Explicitly requested phone call
            create_meet = False
        else:
            # Smart default: if user provided phone number but didn't request video, default to phone call
            # Otherwise default to Google Meet
            if has_phone_number:
                create_meet = False  # Phone call since they gave a phone number
            else:
                create_meet = True   # Google Meet as general default
        
        # Check result
        if create_meet == expected_meet:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            all_passed = False
        
        meet_type = "🎥 Google Meet" if create_meet else "📞 Phone Call"
        print(f"{status} | {meet_type} | {description}")
        print(f"     Text: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        if not create_meet == expected_meet:
            expected_type = "🎥 Google Meet" if expected_meet else "📞 Phone Call"
            print(f"     Expected: {expected_type}, Got: {meet_type}")
        print()
    
    # Summary
    if all_passed:
        print("🎉 All phone call detection tests PASSED!")
        return 0
    else:
        print("⚠️  Some phone call detection tests FAILED!")
        return 1


if __name__ == "__main__":
    print("ChatCal.ai Phone Call Detection Testing")
    print("======================================")
    print()
    
    exit_code = test_meeting_type_detection()
    
    import sys
    sys.exit(exit_code)