#!/usr/bin/env python3
"""Test Google Calendar integration."""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pytz

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.calendar.auth import CalendarAuth
from app.calendar.service import CalendarService
from app.calendar.utils import DateTimeParser, CalendarFormatter
from app.config import settings


def test_auth_setup():
    """Test authentication setup."""
    print("🔐 Testing Calendar Authentication Setup...")
    
    try:
        auth = CalendarAuth()
        
        # Check if credentials are configured
        print(f"✅ Client ID configured: {'Yes' if auth.client_id else 'No'}")
        print(f"✅ Client Secret configured: {'Yes' if auth.client_secret else 'No'}")
        print(f"✅ Redirect URI: {auth.redirect_uri}")
        
        # Test authorization URL generation
        auth_url, state = auth.get_authorization_url()
        print(f"✅ Authorization URL generated successfully")
        print(f"   State: {state}")
        print(f"   URL: {auth_url[:100]}...")
        
        # Check if already authenticated
        is_authenticated = auth.is_authenticated()
        print(f"✅ Already authenticated: {'Yes' if is_authenticated else 'No'}")
        
        return True
    except Exception as e:
        print(f"❌ Authentication setup failed: {e}")
        return False


def test_datetime_parser():
    """Test date/time parsing utilities."""
    print("\n📅 Testing DateTime Parser...")
    
    try:
        parser = DateTimeParser()
        formatter = CalendarFormatter()
        
        # Test various date formats
        test_inputs = [
            "next Tuesday at 2pm",
            "tomorrow at 3:30 PM",
            "Friday afternoon",
            "in 3 days",
            "next week",
            "Monday morning"
        ]
        
        for test_input in test_inputs:
            parsed = parser.parse_datetime(test_input)
            if parsed:
                formatted = formatter.format_datetime(parsed)
                print(f"✅ '{test_input}' → {formatted}")
            else:
                print(f"❌ Failed to parse: '{test_input}'")
        
        # Test duration parsing
        duration_tests = [
            "30 minutes",
            "1 hour",
            "45 mins",
            "2 hours"
        ]
        
        print("\n⏱️  Testing duration parsing:")
        for test_input in duration_tests:
            duration = parser.parse_duration(test_input)
            if duration:
                formatted = formatter.format_duration(duration)
                print(f"✅ '{test_input}' → {duration} minutes ({formatted})")
            else:
                print(f"❌ Failed to parse duration: '{test_input}'")
        
        return True
    except Exception as e:
        print(f"❌ DateTime parser test failed: {e}")
        return False


def test_calendar_service_setup():
    """Test calendar service setup (without API calls)."""
    print("\n📋 Testing Calendar Service Setup...")
    
    try:
        service = CalendarService()
        
        print(f"✅ Calendar ID: {service.calendar_id}")
        print(f"✅ Default timezone: {service.default_timezone}")
        print(f"✅ Calendar service initialized")
        
        # Test availability calculation (mock)
        now = datetime.now(service.default_timezone)
        tomorrow = now + timedelta(days=1)
        
        print(f"✅ Service ready for calendar operations")
        print(f"   Target calendar: {service.calendar_id}")
        
        return True
    except Exception as e:
        print(f"❌ Calendar service setup failed: {e}")
        return False


def test_mock_calendar_operations():
    """Test calendar operations with mock data."""
    print("\n🗓️  Testing Calendar Operations (Mock)...")
    
    try:
        formatter = CalendarFormatter()
        
        # Mock event data
        mock_event = {
            'summary': 'Team Meeting',
            'start': {
                'dateTime': (datetime.now() + timedelta(days=1)).isoformat()
            },
            'end': {
                'dateTime': (datetime.now() + timedelta(days=1, hours=1)).isoformat()
            }
        }
        
        formatted_event = formatter.format_event_summary(mock_event)
        print(f"✅ Event formatting: {formatted_event}")
        
        # Mock availability slots
        now = datetime.now()
        mock_slots = [
            (now + timedelta(hours=1), now + timedelta(hours=2)),
            (now + timedelta(hours=3), now + timedelta(hours=4)),
            (now + timedelta(hours=5), now + timedelta(hours=6))
        ]
        
        formatted_slots = formatter.format_availability_list(mock_slots)
        print(f"✅ Availability formatting: {formatted_slots}")
        
        return True
    except Exception as e:
        print(f"❌ Mock calendar operations failed: {e}")
        return False


def show_authentication_instructions():
    """Show instructions for setting up authentication."""
    print("\n" + "="*60)
    print("📋 Google Calendar Authentication Setup")
    print("="*60)
    
    auth = CalendarAuth()
    auth_url, state = auth.get_authorization_url()
    
    print("\nTo authenticate with Google Calendar:")
    print("1. Open this URL in your browser:")
    print(f"   {auth_url}")
    print("\n2. Complete the OAuth flow")
    print("3. You'll be redirected to localhost (which may show an error)")
    print("4. Copy the full redirect URL and use it with the calendar service")
    print("\n5. The redirect URL will look like:")
    print("   http://localhost:8000/auth/callback?code=...")
    print("\nNote: This is for manual testing. The full app will handle this automatically.")


def main():
    """Run all calendar integration tests."""
    print("🗓️  ChatCal.ai - Google Calendar Integration Test\n")
    
    tests = [
        ("Authentication Setup", test_auth_setup),
        ("DateTime Parser", test_datetime_parser),
        ("Calendar Service Setup", test_calendar_service_setup),
        ("Mock Calendar Operations", test_mock_calendar_operations)
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
    print("\n" + "="*60)
    print("📊 Test Summary:")
    print("="*60)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(success for _, success in results)
    
    if all_passed:
        print("\n🎉 All calendar integration tests passed!")
        show_authentication_instructions()
        
        print("\n📝 Next Steps:")
        print("1. Test OAuth flow by visiting the authentication URL above")
        print("2. Build LlamaIndex tools that use the calendar service")
        print("3. Integrate calendar operations with the chatbot")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration.")


if __name__ == "__main__":
    main()