#!/usr/bin/env python3
"""Test script to verify domain-wide delegation is working."""

import os
import sys
from datetime import datetime, timedelta

def test_domain_delegation():
    """Test domain-wide delegation for calendar access."""
    try:
        # Set production environment
        os.environ['ENVIRONMENT'] = 'production'
        
        from app.calendar.auth import CalendarAuth
        from app.calendar.service import CalendarService
        
        print("🔧 Testing domain-wide delegation...")
        
        # Test authentication
        auth = CalendarAuth()
        print(f"✅ Authentication status: {auth.is_authenticated()}")
        
        # Test service account credentials
        service_creds = auth._get_service_account_credentials()
        if service_creds:
            print(f"✅ Service account credentials loaded with subject: {getattr(service_creds, 'subject', 'None')}")
        else:
            print("❌ Failed to load service account credentials")
            return False
        
        # Test calendar service
        calendar_service = CalendarService()
        service = calendar_service._get_service()
        print(f"✅ Calendar service obtained: {service is not None}")
        
        # Test basic calendar access
        print("\n🔧 Testing calendar access...")
        
        # List calendars accessible by the service account
        calendars = service.calendarList().list().execute()
        calendar_items = calendars.get('items', [])
        print(f"✅ Accessible calendars: {len(calendar_items)}")
        
        for calendar in calendar_items:
            print(f"  - {calendar.get('summary', 'Unknown')}: {calendar.get('id')}")
        
        # Test event listing on primary calendar
        print(f"\n🔧 Testing event listing on Peter's calendar...")
        
        events = calendar_service.list_events(max_results=5)
        print(f"✅ Recent events found: {len(events)}")
        
        for event in events[:3]:  # Show first 3 events
            print(f"  - {event.get('summary', 'No title')}: {event.get('start', {}).get('dateTime', 'No time')}")
        
        # Test event creation (dry run - we'll create and immediately delete)
        print(f"\n🔧 Testing event creation...")
        
        start_time = datetime.now(calendar_service.default_timezone) + timedelta(hours=1)
        end_time = start_time + timedelta(minutes=30)
        
        test_event = calendar_service.create_event(
            summary="ChatCal Domain Delegation Test - DELETE ME",
            start_time=start_time,
            end_time=end_time,
            description="Test event to verify domain-wide delegation is working"
        )
        
        print(f"✅ Test event created successfully!")
        print(f"   Event ID: {test_event.get('id')}")
        print(f"   Event Link: {test_event.get('htmlLink')}")
        
        # Clean up - delete the test event
        calendar_service.delete_event(test_event.get('id'))
        print(f"✅ Test event deleted successfully!")
        
        print(f"\n🎯 Domain-wide delegation is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Domain delegation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_domain_delegation()
    print(f"\n🎯 Overall test result: {'SUCCESS' if success else 'FAILED'}")
    
    if not success:
        print("\n📝 Next steps:")
        print("1. Enable domain-wide delegation in Google Cloud Console")
        print("2. Configure OAuth scopes in Google Admin Console")
        print("3. Wait a few minutes for changes to propagate")
        print("4. Run this test again")