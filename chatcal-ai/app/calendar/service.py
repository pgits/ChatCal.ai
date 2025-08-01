"""Google Calendar service for managing calendar operations."""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
import pytz
from googleapiclient.errors import HttpError
from app.calendar.auth import CalendarAuth
from app.config import settings


class CalendarService:
    """Service for interacting with Google Calendar."""
    
    def __init__(self):
        self.auth = CalendarAuth()
        self.calendar_id = settings.google_calendar_id
        self.default_timezone = pytz.timezone(settings.default_timezone)
    
    def _get_service(self):
        """Get authenticated calendar service."""
        try:
            service = self.auth.get_calendar_service()
            if not service:
                raise RuntimeError("Failed to get calendar service - authentication required")
            return service
        except Exception as e:
            print(f"⚠️ Calendar service error: {e}")
            raise
    
    def list_events(
        self,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 10,
        single_events: bool = True
    ) -> List[Dict]:
        """List calendar events within a time range."""
        try:
            service = self._get_service()
            if not service:
                raise RuntimeError("Calendar service not authenticated")
            
            # Validate inputs
            if max_results < 1 or max_results > 2500:
                raise ValueError("max_results must be between 1 and 2500")
            
            # Default to next 7 days if not specified
            if not time_min:
                time_min = datetime.now(self.default_timezone)
            if not time_max:
                time_max = time_min + timedelta(days=7)
            
            # Validate time range
            if time_min >= time_max:
                raise ValueError("time_min must be before time_max")
            
            # Convert to RFC3339 timestamp
            time_min_str = time_min.isoformat()
            time_max_str = time_max.isoformat()
            
            events_result = service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min_str,
                timeMax=time_max_str,
                maxResults=max_results,
                singleEvents=single_events,
                orderBy='startTime'
            ).execute()
            
            return events_result.get('items', [])
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []
    
    def get_availability(
        self,
        date: datetime,
        duration_minutes: int = 60,
        start_hour: int = 9,
        end_hour: int = 17,
        interval_minutes: int = 30
    ) -> List[Tuple[datetime, datetime]]:
        """Find available time slots on a given date."""
        # Ensure date is timezone-aware
        if date.tzinfo is None:
            date = self.default_timezone.localize(date)
        
        # Set working hours for the day
        start_time = date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        end_time = date.replace(hour=end_hour, minute=0, second=0, microsecond=0)
        
        # Get existing events for the day
        events = self.list_events(
            time_min=start_time,
            time_max=end_time,
            max_results=50
        )
        
        # Build list of busy times
        busy_times = []
        for event in events:
            if 'dateTime' in event.get('start', {}):
                start = datetime.fromisoformat(event['start']['dateTime'])
                end = datetime.fromisoformat(event['end']['dateTime'])
                busy_times.append((start, end))
        
        # Sort busy times
        busy_times.sort(key=lambda x: x[0])
        
        # Find available slots
        available_slots = []
        current_time = start_time
        now = datetime.now(self.default_timezone)
        
        while current_time + timedelta(minutes=duration_minutes) <= end_time:
            slot_end = current_time + timedelta(minutes=duration_minutes)
            
            # Skip slots that are in the past (with 10-minute buffer)
            buffer_time = now + timedelta(minutes=10)
            if current_time <= buffer_time:
                current_time += timedelta(minutes=interval_minutes)
                continue
            
            # Check if this slot conflicts with any busy time
            is_available = True
            for busy_start, busy_end in busy_times:
                if not (slot_end <= busy_start or current_time >= busy_end):
                    is_available = False
                    break
            
            if is_available:
                available_slots.append((current_time, slot_end))
            
            # Move to next interval
            current_time += timedelta(minutes=interval_minutes)
        
        return available_slots
    
    def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        location: Optional[str] = None,
        send_notifications: bool = True,
        create_meet_conference: bool = False
    ) -> Dict:
        """Create a new calendar event."""
        service = self._get_service()
        
        # Ensure times are timezone-aware
        if start_time.tzinfo is None:
            start_time = self.default_timezone.localize(start_time)
        if end_time.tzinfo is None:
            end_time = self.default_timezone.localize(end_time)
        
        event = {
            'summary': summary,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': str(self.default_timezone),
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': str(self.default_timezone),
            },
        }
        
        if description:
            event['description'] = description
        
        if location:
            event['location'] = location
        
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
        
        # Add Google Meet conference if requested
        if create_meet_conference:
            import uuid
            event['conferenceData'] = {
                'createRequest': {
                    'requestId': str(uuid.uuid4()),  # Generate unique request ID
                    'conferenceSolutionKey': {
                        'type': 'hangoutsMeet'
                    }
                }
            }
        
        try:
            # Use conferenceDataVersion=1 if creating a Meet conference
            conference_version = 1 if create_meet_conference else None
            
            created_event = service.events().insert(
                calendarId=self.calendar_id,
                body=event,
                sendNotifications=send_notifications,
                conferenceDataVersion=conference_version
            ).execute()
            
            return created_event
        
        except HttpError as error:
            print(f'An error occurred: {error}')
            raise
    
    def update_event(
        self,
        event_id: str,
        updates: Dict,
        send_notifications: bool = True
    ) -> Dict:
        """Update an existing calendar event."""
        service = self._get_service()
        
        try:
            # Get the existing event
            event = service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            # Apply updates
            event.update(updates)
            
            # Update the event
            updated_event = service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event,
                sendNotifications=send_notifications
            ).execute()
            
            return updated_event
        
        except HttpError as error:
            print(f'An error occurred: {error}')
            raise
    
    def delete_event(
        self,
        event_id: str,
        send_notifications: bool = True
    ) -> bool:
        """Delete a calendar event."""
        service = self._get_service()
        
        try:
            service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id,
                sendNotifications=send_notifications
            ).execute()
            
            return True
        
        except HttpError as error:
            print(f'An error occurred: {error}')
            return False
    
    def get_event(self, event_id: str) -> Optional[Dict]:
        """Get a specific event by ID."""
        service = self._get_service()
        
        try:
            event = service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            return event
        
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None
    
    def check_conflicts(
        self,
        start_time: datetime,
        end_time: datetime,
        exclude_event_id: Optional[str] = None
    ) -> List[Dict]:
        """Check for conflicting events in the given time range."""
        events = self.list_events(
            time_min=start_time,
            time_max=end_time,
            max_results=50
        )
        
        conflicts = []
        for event in events:
            # Skip if this is the event we're updating
            if exclude_event_id and event.get('id') == exclude_event_id:
                continue
            
            # Check for overlap
            if 'dateTime' in event.get('start', {}):
                event_start = datetime.fromisoformat(event['start']['dateTime'])
                event_end = datetime.fromisoformat(event['end']['dateTime'])
                
                # Check if there's an overlap
                if not (end_time <= event_start or start_time >= event_end):
                    conflicts.append(event)
        
        return conflicts