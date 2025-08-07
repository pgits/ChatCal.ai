"""Calendar utility functions for date/time parsing and formatting."""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict
import pytz
from dateutil import parser
from dateutil.relativedelta import relativedelta
from app.config import settings


class DateTimeParser:
    """Utility class for parsing natural language date/time expressions."""
    
    def __init__(self, default_timezone: str = None):
        self.default_timezone = pytz.timezone(default_timezone or settings.default_timezone)
        self.now = datetime.now(self.default_timezone)
    
    def parse_datetime(self, text: str) -> Optional[datetime]:
        """Parse various datetime formats from natural language."""
        text = text.lower().strip()
        
        # Handle relative dates first (e.g., "tomorrow at 3pm", "today at 2pm")
        # This must come before dateutil parsing because dateutil ignores "tomorrow"
        relative_date = self._parse_relative_date(text)
        if relative_date:
            return relative_date
        
        # Handle day names
        day_date = self._parse_day_name(text)
        if day_date:
            return day_date
        
        # Try standard parsing as fallback
        try:
            dt = parser.parse(text, fuzzy=True)
            if dt.tzinfo is None:
                dt = self.default_timezone.localize(dt)
            return dt
        except:
            pass
        
        return None
    
    def _parse_relative_date(self, text: str) -> Optional[datetime]:
        """Parse relative dates like 'tomorrow', 'next week', etc."""
        base_time = self.now.replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Extract time component if present (e.g., "at 3pm", "at 10:30am")
        time_match = re.search(r'at\s+(\d{1,2}):?(\d{2})?\s*(am|pm)|at\s+(\d{1,2})\s*(am|pm)', text.lower())
        if time_match:
            if time_match.group(1):  # Format: "at 3:30pm" or "at 15:30"
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                period = time_match.group(3)
            else:  # Format: "at 3pm"
                hour = int(time_match.group(4))
                minute = 0
                period = time_match.group(5)
            
            # Convert to 24-hour format
            if period:
                if period.lower() == 'pm' and hour != 12:
                    hour += 12
                elif period.lower() == 'am' and hour == 12:
                    hour = 0
            
            base_time = base_time.replace(hour=hour, minute=minute)
        
        # Today/tonight
        if any(word in text for word in ['today', 'tonight']):
            return base_time
        
        # Tomorrow
        if 'tomorrow' in text:
            return base_time + timedelta(days=1)
        
        # Yesterday
        if 'yesterday' in text:
            return base_time - timedelta(days=1)
        
        # Next week
        if 'next week' in text:
            days_ahead = 7 - base_time.weekday()
            return base_time + timedelta(days=days_ahead)
        
        # This week
        if 'this week' in text:
            return base_time
        
        # Next month
        if 'next month' in text:
            return base_time + relativedelta(months=1)
        
        # In X days/weeks/months
        match = re.search(r'in (\d+) (day|week|month)s?', text)
        if match:
            number = int(match.group(1))
            unit = match.group(2)
            
            if unit == 'day':
                return base_time + timedelta(days=number)
            elif unit == 'week':
                return base_time + timedelta(weeks=number)
            elif unit == 'month':
                return base_time + relativedelta(months=number)
        
        return None
    
    def _parse_day_name(self, text: str) -> Optional[datetime]:
        """Parse day names like 'monday', 'next tuesday', etc."""
        days = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        for day_name, day_num in days.items():
            if day_name in text:
                current_day = self.now.weekday()
                days_ahead = day_num - current_day
                
                # If it's the same day, assume next week if "next" is mentioned
                if days_ahead <= 0 or 'next' in text:
                    days_ahead += 7
                
                target_date = self.now + timedelta(days=days_ahead)
                return target_date.replace(hour=9, minute=0, second=0, microsecond=0)
        
        return None
    
    def parse_time(self, text: str) -> Optional[Tuple[int, int]]:
        """Parse time from text, returning (hour, minute) tuple."""
        text = text.lower().strip()
        
        # Handle AM/PM format
        am_pm_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', text)
        if am_pm_match:
            hour = int(am_pm_match.group(1))
            minute = int(am_pm_match.group(2)) if am_pm_match.group(2) else 0
            is_pm = am_pm_match.group(3) == 'pm'
            
            if is_pm and hour != 12:
                hour += 12
            elif not is_pm and hour == 12:
                hour = 0
            
            return (hour, minute)
        
        # Handle 24-hour format
        time_match = re.search(r'(\d{1,2}):(\d{2})', text)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            return (hour, minute)
        
        # Handle hour-only format
        hour_match = re.search(r'(\d{1,2})\s*(?:o\'?clock)?', text)
        if hour_match:
            hour = int(hour_match.group(1))
            # Assume afternoon for business hours
            if 8 <= hour <= 12:
                return (hour, 0)
            elif 1 <= hour <= 7:
                return (hour + 12, 0)
        
        return None
    
    def parse_duration(self, text: str) -> Optional[int]:
        """Parse duration in minutes from text."""
        text = text.lower().strip()
        
        # Handle "X hours" or "X hour"
        hour_match = re.search(r'(\d+(?:\.\d+)?)\s*hours?', text)
        if hour_match:
            hours = float(hour_match.group(1))
            return int(hours * 60)
        
        # Handle "X minutes" or "X mins"
        minute_match = re.search(r'(\d+)\s*(?:minutes?|mins?)', text)
        if minute_match:
            return int(minute_match.group(1))
        
        # Handle common durations
        if '30' in text or 'thirty' in text or 'half' in text:
            return 30
        elif '15' in text or 'fifteen' in text or 'quarter' in text:
            return 15
        elif '45' in text or 'forty-five' in text:
            return 45
        elif '60' in text or 'hour' in text:
            return 60
        elif '90' in text or 'ninety' in text:
            return 90
        elif '120' in text or 'two hour' in text:
            return 120
        
        return None


class CalendarFormatter:
    """Utility class for formatting calendar information."""
    
    def __init__(self, timezone: str = None):
        self.timezone = pytz.timezone(timezone or settings.default_timezone)
    
    def format_datetime(self, dt: datetime, include_date: bool = True) -> str:
        """Format datetime in a user-friendly way."""
        if dt.tzinfo is None:
            dt = self.timezone.localize(dt)
        else:
            dt = dt.astimezone(self.timezone)
        
        # Format time
        time_str = dt.strftime("%-I:%M %p" if dt.minute else "%-I %p")
        
        if not include_date:
            return time_str
        
        # Format date
        today = datetime.now(self.timezone).date()
        tomorrow = today + timedelta(days=1)
        yesterday = today - timedelta(days=1)
        
        if dt.date() == today:
            return f"today at {time_str}"
        elif dt.date() == tomorrow:
            return f"tomorrow at {time_str}"
        elif dt.date() == yesterday:
            return f"yesterday at {time_str}"
        else:
            # Check if it's this week
            days_diff = (dt.date() - today).days
            if 0 < days_diff <= 7:
                day_name = dt.strftime("%A")
                return f"{day_name} at {time_str}"
            else:
                date_str = dt.strftime("%B %-d")
                if dt.year != today.year:
                    date_str += f", {dt.year}"
                return f"{date_str} at {time_str}"
    
    def format_duration(self, minutes: int) -> str:
        """Format duration in a user-friendly way."""
        if minutes < 60:
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        if remaining_minutes == 0:
            return f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            return f"{hours} hour{'s' if hours != 1 else ''} and {remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}"
    
    def format_availability_list(self, slots: List[Tuple[datetime, datetime]]) -> str:
        """Format list of available time slots."""
        if not slots:
            return "No available time slots found."
        
        formatted_slots = []
        for start, end in slots:
            start_str = self.format_datetime(start, include_date=False)
            end_str = self.format_datetime(end, include_date=False)
            formatted_slots.append(f"{start_str} - {end_str}")
        
        if len(formatted_slots) <= 3:
            return ", ".join(formatted_slots)
        else:
            first_three = ", ".join(formatted_slots[:3])
            remaining = len(formatted_slots) - 3
            return f"{first_three}, and {remaining} more slot{'s' if remaining != 1 else ''}"
    
    def format_event_summary(self, event: Dict) -> str:
        """Format a calendar event for display."""
        summary = event.get('summary', 'Untitled Event')
        
        if 'start' in event and 'dateTime' in event['start']:
            start = datetime.fromisoformat(event['start']['dateTime'])
            start_str = self.format_datetime(start)
            
            if 'end' in event and 'dateTime' in event['end']:
                end = datetime.fromisoformat(event['end']['dateTime'])
                duration = int((end - start).total_seconds() / 60)
                duration_str = self.format_duration(duration)
                
                return f"{summary} ({start_str}, {duration_str})"
            else:
                return f"{summary} ({start_str})"
        
        return summary