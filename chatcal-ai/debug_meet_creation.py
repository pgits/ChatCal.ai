#!/usr/bin/env python3
"""Debug script to test Google Meet link creation."""

import os
import sys
import json
from datetime import datetime, timedelta

# Add the app directory to Python path
sys.path.insert(0, '/Users/petergits/dev/chatCal.ai/chatcal-ai')

from app.calendar.service import CalendarService
from app.calendar.auth import CalendarAuth
from app.config import settings

def debug_meet_creation():
    """Test Google Meet link creation in calendar events."""
    
    print("🔍 Testing Google Meet link creation...")
    
    # Initialize calendar service
    try:
        calendar_service = CalendarService()
        print("✅ Calendar service initialized")
    except Exception as e:
        print(f"❌ Failed to initialize calendar service: {e}")
        return
    
    # Test event creation with Google Meet
    try:
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(minutes=30)
        
        print(f"📅 Creating test event from {start_time} to {end_time}")
        
        event = calendar_service.create_event(
            summary="Debug Google Meet Test",
            start_time=start_time,
            end_time=end_time,
            description="Testing Google Meet link creation",
            create_meet_conference=True
        )
        
        print("✅ Event created successfully!")
        print("📋 Event details:")
        print(json.dumps(event, indent=2, default=str))
        
        # Check for Google Meet link
        if 'conferenceData' in event:
            print("\n🎥 Conference data found:")
            conf_data = event['conferenceData']
            print(json.dumps(conf_data, indent=2, default=str))
            
            if 'entryPoints' in conf_data:
                meet_entries = conf_data['entryPoints']
                meet_link = next((entry['uri'] for entry in meet_entries if entry['entryPointType'] == 'video'), None)
                if meet_link:
                    print(f"\n✅ Google Meet link found: {meet_link}")
                else:
                    print("\n⚠️ No video entry point found in conference data")
            else:
                print("\n⚠️ No entry points found in conference data")
        else:
            print("\n❌ No conferenceData found in event")
            
    except Exception as e:
        print(f"❌ Failed to create event: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_meet_creation()