"""Working hours validation for calendar bookings."""

import os
from datetime import datetime, time
from typing import Optional, Tuple
import pytz

from app.config import settings


class WorkingHoursValidator:
    """Validates appointment times against configured working hours."""
    
    def __init__(self):
        """Initialize working hours validator with configuration."""
        self.timezone = pytz.timezone(settings.working_hours_timezone)
        
        # Parse weekday hours (Monday-Friday)
        self.weekday_start = self._parse_time(settings.weekday_start_time)
        self.weekday_end = self._parse_time(settings.weekday_end_time)
        
        # Parse weekend hours (Saturday-Sunday)
        self.weekend_start = self._parse_time(settings.weekend_start_time)
        self.weekend_end = self._parse_time(settings.weekend_end_time)
    
    def _parse_time(self, time_str: str) -> time:
        """Parse time string in HH:MM format to time object."""
        try:
            hour, minute = map(int, time_str.split(':'))
            return time(hour, minute)
        except (ValueError, AttributeError):
            # Default fallback times
            if "start" in time_str.lower():
                return time(9, 0)  # 9:00 AM
            else:
                return time(17, 0)  # 5:00 PM
    
    def is_within_working_hours(self, appointment_datetime: datetime) -> Tuple[bool, str]:
        """
        Check if appointment time is within working hours.
        
        Args:
            appointment_datetime: The proposed appointment datetime
            
        Returns:
            Tuple of (is_valid, error_message_if_invalid)
        """
        # Convert to working hours timezone if needed
        if appointment_datetime.tzinfo is None:
            # Assume it's in the default timezone
            appointment_datetime = self.timezone.localize(appointment_datetime)
        elif appointment_datetime.tzinfo != self.timezone:
            appointment_datetime = appointment_datetime.astimezone(self.timezone)
        
        # Get day of week (0=Monday, 6=Sunday)
        weekday = appointment_datetime.weekday()
        appointment_time = appointment_datetime.time()
        
        # Check if it's weekend (Saturday=5, Sunday=6)
        if weekday >= 5:  # Weekend
            if self.weekend_start <= appointment_time <= self.weekend_end:
                return True, ""
            else:
                working_hours = self._format_working_hours_message(is_weekend=True)
                return False, f"My apologies for the inconvenience, but Pete's business hours are {working_hours}."
        else:  # Weekday
            if self.weekday_start <= appointment_time <= self.weekday_end:
                return True, ""
            else:
                working_hours = self._format_working_hours_message(is_weekend=False)
                return False, f"My apologies for the inconvenience, but Pete's business hours are {working_hours}."
    
    def _format_working_hours_message(self, is_weekend: bool = False) -> str:
        """Format working hours for user-friendly message."""
        if is_weekend:
            start_str = self._format_time_12hr(self.weekend_start)
            end_str = self._format_time_12hr(self.weekend_end)
            return f"Saturday and Sunday from {start_str} - {end_str} EDT"
        else:
            start_str = self._format_time_12hr(self.weekday_start)
            end_str = self._format_time_12hr(self.weekday_end)
            return f"Monday through Friday from {start_str} - {end_str} EDT"
    
    def _format_time_12hr(self, time_obj: time) -> str:
        """Format time object to 12-hour format string."""
        return time_obj.strftime("%I:%M %p").lstrip('0')
    
    def get_full_working_hours_message(self) -> str:
        """Get complete working hours information."""
        weekday_hours = self._format_working_hours_message(is_weekend=False)
        weekend_hours = self._format_working_hours_message(is_weekend=True)
        
        return (
            f"Pete's business hours are:\n"
            f"• {weekday_hours}\n"
            f"• {weekend_hours}"
        )
    
    def get_suggested_times(self, requested_date: datetime) -> str:
        """Get suggested available times for a given date."""
        # Convert to working hours timezone
        if requested_date.tzinfo is None:
            requested_date = self.timezone.localize(requested_date)
        elif requested_date.tzinfo != self.timezone:
            requested_date = requested_date.astimezone(self.timezone)
        
        weekday = requested_date.weekday()
        
        if weekday >= 5:  # Weekend
            start_time = self.weekend_start
            end_time = self.weekend_end
            day_type = "weekend"
        else:  # Weekday
            start_time = self.weekday_start
            end_time = self.weekday_end
            day_type = "weekday"
        
        start_str = self._format_time_12hr(start_time)
        end_str = self._format_time_12hr(end_time)
        
        return (
            f"For {requested_date.strftime('%A, %B %d')}, Pete is available "
            f"between {start_str} and {end_str} EDT. "
            f"Please suggest a specific time within this window."
        )


# Global instance for use throughout the application
working_hours_validator = WorkingHoursValidator()