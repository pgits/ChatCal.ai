#!/usr/bin/env python3
"""Test script for working hours validation functionality."""

import os
import sys
from datetime import datetime, time
import pytz

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.working_hours import working_hours_validator


def test_working_hours():
    """Test various working hours scenarios."""
    
    print("🕐 Testing Working Hours Validation")
    print("=" * 50)
    
    # Set up timezone for testing
    tz = pytz.timezone("America/New_York")
    
    # Test cases with expected results
    test_cases = [
        # Weekday tests (Monday = 0, Friday = 4)
        ("Monday 8:00 AM", datetime(2024, 1, 8, 8, 0), True, "Within weekday hours"),
        ("Monday 6:00 AM", datetime(2024, 1, 8, 6, 0), False, "Before weekday hours"),
        ("Monday 7:00 PM", datetime(2024, 1, 8, 19, 0), False, "After weekday hours"),
        ("Friday 2:00 PM", datetime(2024, 1, 12, 14, 0), True, "Within weekday hours"),
        
        # Weekend tests (Saturday = 5, Sunday = 6)  
        ("Saturday 11:00 AM", datetime(2024, 1, 13, 11, 0), True, "Within weekend hours"),
        ("Saturday 9:00 AM", datetime(2024, 1, 13, 9, 0), False, "Before weekend hours"),
        ("Saturday 5:00 PM", datetime(2024, 1, 13, 17, 0), False, "After weekend hours"),
        ("Sunday 3:00 PM", datetime(2024, 1, 14, 15, 0), True, "Within weekend hours"),
        
        # Edge cases
        ("Monday 7:30 AM", datetime(2024, 1, 8, 7, 30), True, "Exact weekday start time"),
        ("Monday 6:30 PM", datetime(2024, 1, 8, 18, 30), True, "Exact weekday end time"),
        ("Saturday 10:30 AM", datetime(2024, 1, 13, 10, 30), True, "Exact weekend start time"),
        ("Saturday 4:30 PM", datetime(2024, 1, 13, 16, 30), True, "Exact weekend end time"),
    ]
    
    print("Current Working Hours Configuration:")
    print(working_hours_validator.get_full_working_hours_message())
    print()
    
    all_passed = True
    
    for description, test_time, expected_valid, test_type in test_cases:
        # Localize the test time
        localized_time = tz.localize(test_time)
        
        # Test the validation
        is_valid, error_message = working_hours_validator.is_within_working_hours(localized_time)
        
        # Check if result matches expectation
        if is_valid == expected_valid:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            all_passed = False
        
        print(f"{status} | {description:<20} | {test_type}")
        if not is_valid and error_message:
            print(f"     Error: {error_message}")
        print()
    
    # Test suggested times functionality
    print("🕒 Testing Suggested Times")
    print("=" * 30)
    
    # Test weekday suggestion
    monday = tz.localize(datetime(2024, 1, 8, 12, 0))  # Monday noon
    suggestion = working_hours_validator.get_suggested_times(monday)
    print("Monday suggestion:")
    print(f"  {suggestion}")
    print()
    
    # Test weekend suggestion
    saturday = tz.localize(datetime(2024, 1, 13, 12, 0))  # Saturday noon
    suggestion = working_hours_validator.get_suggested_times(saturday)
    print("Saturday suggestion:")
    print(f"  {suggestion}")
    print()
    
    # Final result
    if all_passed:
        print("🎉 All working hours validation tests PASSED!")
        return 0
    else:
        print("⚠️  Some working hours validation tests FAILED!")
        return 1


def test_integration():
    """Test integration with the calendar tools."""
    print("🔧 Testing Integration with Calendar Tools")
    print("=" * 40)
    
    try:
        from app.core.tools import CalendarTools
        
        # Create calendar tools instance
        tools = CalendarTools()
        
        # Test booking outside working hours
        print("Testing booking outside working hours...")
        result = tools.create_appointment(
            title="Test Meeting",
            date_string="next Monday",
            time_string="6:00 AM",  # Before working hours
            duration_minutes=30,
            user_name="Test User",
            user_email="test@example.com"
        )
        
        print("Result:", result)
        
        # Check if the error message contains working hours info
        if "Pete's business hours are" in result:
            print("✅ Working hours validation integrated successfully")
        else:
            print("❌ Working hours validation not properly integrated")
            
    except ImportError as e:
        print(f"⚠️  Could not import CalendarTools for integration test: {e}")
    except Exception as e:
        print(f"❌ Integration test failed: {e}")


if __name__ == "__main__":
    print("ChatCal.ai Working Hours Testing")
    print("=================================")
    print()
    
    # Test working hours validation
    exit_code = test_working_hours()
    
    # Test integration
    test_integration()
    
    sys.exit(exit_code)