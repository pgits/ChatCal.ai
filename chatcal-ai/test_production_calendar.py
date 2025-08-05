#!/usr/bin/env python3
"""Test script to debug production calendar service issues."""

import os
import sys
import json
from datetime import datetime, timedelta

def test_calendar_service():
    """Test calendar service authentication and basic operations."""
    try:
        # Import after setting environment 
        os.environ['ENVIRONMENT'] = 'production'
        
        from app.calendar.service import CalendarService
        from app.calendar.auth import CalendarAuth
        
        print("🔧 Testing production calendar service...")
        
        # Test authentication
        auth = CalendarAuth()
        print(f"✅ Authentication status: {auth.is_authenticated()}")
        
        # Test service creation
        calendar_service = CalendarService()
        print(f"✅ Calendar service created")
        
        # Test getting calendar service
        service = calendar_service.auth.get_calendar_service()
        print(f"✅ Calendar service obtained: {service is not None}")
        
        # Test basic API call - list calendars
        calendars = service.calendarList().list().execute()
        calendar_items = calendars.get('items', [])
        print(f"✅ Accessible calendars: {len(calendar_items)}")
        
        for calendar in calendar_items:
            print(f"  - {calendar.get('summary', 'Unknown')}: {calendar.get('id')}")
            
        # Test event creation (dry run)
        print("\n🔧 Testing event creation...")
        
        # Get current time + 1 hour for test
        start_time = datetime.now(calendar_service.default_timezone) + timedelta(hours=1)
        end_time = start_time + timedelta(minutes=30)
        
        # Try to create a test event
        test_event = {
            'summary': 'ChatCal Test Event - DELETE ME',
            'description': 'Test event created by ChatCal debugging script',
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': str(calendar_service.default_timezone),
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': str(calendar_service.default_timezone),
            },
        }
        
        # Use primary calendar
        calendar_id = 'primary'
        created_event = service.events().insert(calendarId=calendar_id, body=test_event).execute()
        
        print(f"✅ Test event created successfully!")
        print(f"   Event ID: {created_event.get('id')}")
        print(f"   Event Link: {created_event.get('htmlLink')}")
        
        # Clean up - delete the test event
        service.events().delete(calendarId=calendar_id, eventId=created_event.get('id')).execute()
        print(f"✅ Test event deleted successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Calendar service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_calendar_service()
    print(f"\n🎯 Overall test result: {'SUCCESS' if success else 'FAILED'}")