"""LlamaIndex tools for calendar operations."""

from typing import List, Optional, Dict
from datetime import datetime, timedelta
from llama_index.core.tools import FunctionTool
from app.calendar.service import CalendarService
from app.calendar.utils import DateTimeParser, CalendarFormatter
from app.personality.prompts import BOOKING_CONFIRMATIONS, ERROR_RESPONSES
from app.core.email_service import email_service
from app.config import settings
import random


class CalendarTools:
    """LlamaIndex tools for calendar operations."""
    
    def __init__(self, agent=None):
        self.calendar_service = CalendarService()
        self.datetime_parser = DateTimeParser()
        self.formatter = CalendarFormatter()
        self.agent = agent  # Reference to the ChatCalAgent for user info
    
    def check_availability(
        self,
        date_string: str,
        duration_minutes: int = 60,
        preferred_time: Optional[str] = None
    ) -> str:
        """
        Check availability for a given date and return available time slots.
        
        Args:
            date_string: Natural language date (e.g., "next Tuesday", "tomorrow")
            duration_minutes: Meeting duration in minutes (default: 60)
            preferred_time: Preferred time if specified (e.g., "2pm", "morning")
        
        Returns:
            Formatted string with available time slots
        """
        try:
            # Parse the date
            target_date = self.datetime_parser.parse_datetime(date_string)
            if not target_date:
                return "I'm having trouble understanding that date. Could you try rephrasing it? For example: 'next Tuesday' or 'tomorrow'"
            
            # Get availability
            slots = self.calendar_service.get_availability(
                date=target_date,
                duration_minutes=duration_minutes
            )
            
            if not slots:
                return f"Unfortunately, I don't see any available {self.formatter.format_duration(duration_minutes)} slots on {self.formatter.format_datetime(target_date, include_date=False)}. Would you like to try a different day?"
            
            # Filter by preferred time if specified
            if preferred_time:
                time_tuple = self.datetime_parser.parse_time(preferred_time)
                if time_tuple:
                    preferred_hour, preferred_minute = time_tuple
                    filtered_slots = []
                    for start, end in slots:
                        if abs(start.hour - preferred_hour) <= 2:  # Within 2 hours
                            filtered_slots.append((start, end))
                    if filtered_slots:
                        slots = filtered_slots
            
            date_str = self.formatter.format_datetime(target_date, include_date=True).split(" at ")[0]
            availability_str = self.formatter.format_availability_list(slots)
            
            return f"Great news! Here are the available {self.formatter.format_duration(duration_minutes)} slots for {date_str}: {availability_str}. Which time works best for you?"
            
        except Exception as e:
            return f"I'm having a bit of trouble checking your calendar right now. Could you try again? (Error: {str(e)})"
    
    def create_appointment(
        self,
        title: str,
        date_string: str,
        time_string: str,
        duration_minutes: int = 60,
        description: Optional[str] = None,
        attendee_emails: Optional[List[str]] = None,
        user_name: str = None,
        user_phone: str = None,
        user_email: str = None,
        create_meet_conference: bool = False
    ) -> str:
        """
        Create a new calendar appointment with email invitations.
        
        Args:
            title: Meeting title/summary
            date_string: Date in natural language
            time_string: Time in natural language  
            duration_minutes: Duration in minutes
            description: Optional meeting description
            attendee_emails: Optional list of attendee email addresses
            user_name: User's full name
            user_phone: User's phone number
            user_email: User's email address
            create_meet_conference: Whether to create a Google Meet conference
        
        Returns:
            Confirmation message or error
        """
        try:
            # Parse date and time
            datetime_str = f"{date_string} at {time_string}"
            start_time = self.datetime_parser.parse_datetime(datetime_str)
            
            if not start_time:
                return "I'm having trouble understanding that date and time. Could you clarify? For example: 'next Tuesday at 2pm'"
            
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            # Check for conflicts
            conflicts = self.calendar_service.check_conflicts(start_time, end_time)
            if conflicts:
                conflict_summaries = [event.get('summary', 'Untitled') for event in conflicts]
                return f"Oops! You already have {', '.join(conflict_summaries)} scheduled at that time. How about we find a different slot?"
            
            # Create the event
            event = self.calendar_service.create_event(
                summary=title,
                start_time=start_time,
                end_time=end_time,
                description=description,
                attendees=attendee_emails or [],
                create_meet_conference=create_meet_conference
            )
            
            # Format confirmation
            formatted_time = self.formatter.format_datetime(start_time)
            duration_str = self.formatter.format_duration(duration_minutes)
            
            # Extract Google Meet link if conference was created
            meet_link = ""
            if create_meet_conference and 'conferenceData' in event and 'entryPoints' in event['conferenceData']:
                meet_entries = event['conferenceData']['entryPoints']
                meet_link = next((entry['uri'] for entry in meet_entries if entry['entryPointType'] == 'video'), "")
            
            # Send email invitations
            email_sent_to_user = False
            email_sent_to_peter = False
            
            # Send email to Peter (always)
            try:
                email_sent_to_peter = email_service.send_invitation_email(
                    to_email=settings.my_email_address,
                    to_name="Peter Michael Gits",
                    title=title,
                    start_datetime=start_time,
                    end_datetime=end_time,
                    description=description or "",
                    user_phone=user_phone or "",
                    meeting_type=title,
                    meet_link=meet_link
                )
            except Exception as e:
                print(f"Failed to send email to Peter: {e}")
            
            # Send email to user if they provided email
            if user_email:
                try:
                    email_sent_to_user = email_service.send_invitation_email(
                        to_email=user_email,
                        to_name=user_name or "Guest",
                        title=title,
                        start_datetime=start_time,
                        end_datetime=end_time,
                        description=description or "",
                        user_phone=user_phone or "",
                        meeting_type=title,
                        meet_link=meet_link
                    )
                except Exception as e:
                    print(f"Failed to send email to user: {e}")
            
            # Use random confirmation message
            confirmation_template = random.choice(BOOKING_CONFIRMATIONS)
            confirmation = confirmation_template.format(
                meeting_type=title,
                attendee=user_name or "your meeting",
                date=formatted_time.split(" at ")[0],
                time=formatted_time.split(" at ")[1]
            )
            
            # Add email status to confirmation
            email_status = ""
            if user_email and email_sent_to_user:
                email_status = "\n\n📧 Calendar invitations have been sent to both you and Peter via email."
            elif user_email and not email_sent_to_user:
                email_status = "\n\n📧 Email invitation sent to Peter. There was an issue sending your invitation, but the meeting is confirmed."
            elif not user_email:
                email_status = "\n\n📧 If you'd like me to send you a calendar invitation via email, please provide your email address."
            
            # Add Google Meet information if conference was created
            meet_info = ""
            if create_meet_conference:
                # Extract Meet link from the created event
                if 'conferenceData' in event and 'entryPoints' in event['conferenceData']:
                    meet_entries = event['conferenceData']['entryPoints']
                    meet_link = next((entry['uri'] for entry in meet_entries if entry['entryPointType'] == 'video'), None)
                    if meet_link:
                        meet_info = f"\n\n🎥 Google Meet link: {meet_link}"
                    else:
                        meet_info = "\n\n🎥 Google Meet conference call has been set up (link will be available in your calendar)."
                else:
                    meet_info = "\n\n🎥 Google Meet conference call has been set up (link will be available in your calendar)."
            
            return f"{confirmation} The meeting is set for {duration_str}.{email_status}{meet_info}"
            
        except Exception as e:
            return f"I'm having trouble creating that appointment right now. Could you try again? (Error: {str(e)})"
    
    def list_upcoming_events(self, days_ahead: int = 7) -> str:
        """
        List upcoming events in the next specified days.
        
        Args:
            days_ahead: Number of days to look ahead (default: 7)
        
        Returns:
            Formatted list of upcoming events
        """
        try:
            now = datetime.now(self.calendar_service.default_timezone)
            end_time = now + timedelta(days=days_ahead)
            
            events = self.calendar_service.list_events(
                time_min=now,
                time_max=end_time,
                max_results=20
            )
            
            if not events:
                return f"You have a completely clear schedule for the next {days_ahead} day{'s' if days_ahead != 1 else ''}! Perfect time to book some meetings! 📅"
            
            formatted_events = []
            for event in events[:10]:  # Limit to 10 events
                event_summary = self.formatter.format_event_summary(event)
                formatted_events.append(f"• {event_summary}")
            
            events_list = "\n".join(formatted_events)
            total_count = len(events)
            
            if total_count > 10:
                events_list += f"\n• ... and {total_count - 10} more events"
            
            period = f"next {days_ahead} day{'s' if days_ahead != 1 else ''}"
            return f"Here's what's coming up in the {period}:\n\n{events_list}"
            
        except Exception as e:
            return f"I'm having trouble accessing your calendar right now. Could you try again? (Error: {str(e)})"
    
    def reschedule_appointment(
        self,
        original_date_time: str,
        new_date_string: str,
        new_time_string: str
    ) -> str:
        """
        Reschedule an existing appointment.
        
        Args:
            original_date_time: Original appointment date/time to find
            new_date_string: New date in natural language
            new_time_string: New time in natural language
        
        Returns:
            Confirmation message or error
        """
        try:
            # Parse original date/time to find the event
            original_dt = self.datetime_parser.parse_datetime(original_date_time)
            if not original_dt:
                return "I'm having trouble finding that appointment. Could you be more specific about the original date and time?"
            
            # Find events around that time
            search_start = original_dt - timedelta(hours=1)
            search_end = original_dt + timedelta(hours=1)
            
            events = self.calendar_service.list_events(
                time_min=search_start,
                time_max=search_end,
                max_results=5
            )
            
            if not events:
                return "I couldn't find any appointments around that time. Could you check your calendar and try again?"
            
            # For now, take the first matching event (in a real implementation, 
            # we might want to present options to the user)
            event_to_update = events[0]
            
            # Parse new date/time
            new_datetime_str = f"{new_date_string} at {new_time_string}"
            new_start_time = self.datetime_parser.parse_datetime(new_datetime_str)
            
            if not new_start_time:
                return "I'm having trouble understanding the new date and time. Could you clarify?"
            
            # Calculate new end time based on original duration
            if 'start' in event_to_update and 'end' in event_to_update:
                original_start = datetime.fromisoformat(event_to_update['start']['dateTime'])
                original_end = datetime.fromisoformat(event_to_update['end']['dateTime'])
                duration = original_end - original_start
                new_end_time = new_start_time + duration
            else:
                new_end_time = new_start_time + timedelta(hours=1)  # Default 1 hour
            
            # Check for conflicts at new time
            conflicts = self.calendar_service.check_conflicts(
                new_start_time, 
                new_end_time,
                exclude_event_id=event_to_update.get('id')
            )
            
            if conflicts:
                return "The new time conflicts with another appointment. Could you suggest a different time?"
            
            # Update the event
            updates = {
                'start': {
                    'dateTime': new_start_time.isoformat(),
                    'timeZone': str(self.calendar_service.default_timezone),
                },
                'end': {
                    'dateTime': new_end_time.isoformat(),
                    'timeZone': str(self.calendar_service.default_timezone),
                }
            }
            
            self.calendar_service.update_event(event_to_update['id'], updates)
            
            old_time = self.formatter.format_datetime(original_dt)
            new_time = self.formatter.format_datetime(new_start_time)
            
            return f"Perfect! I've rescheduled your appointment from {old_time} to {new_time}. All set! 🎉"
            
        except Exception as e:
            return f"I'm having trouble rescheduling that appointment. Could you try again? (Error: {str(e)})"

    def create_appointment_with_user_info(
        self,
        title: str,
        date_string: str,
        time_string: str,
        duration_minutes: int = 60,
        description: Optional[str] = None
    ) -> str:
        """Create appointment using stored user information from agent."""
        if not self.agent:
            return "Internal error: No agent reference available."
        
        user_info = self.agent.get_user_info()
        
        # Check if we have required user information
        if not self.agent.has_complete_user_info():
            missing = self.agent.get_missing_user_info()
            if "contact (email OR phone)" in missing:
                return f"I cannot book any appointments without your contact information. I need either your email address or phone number. Which would you prefer to share? Alternatively, you can call Peter directly at {settings.my_phone_number}."
            if "name" in missing:
                return "I cannot book any appointment without your name. May I have your name?"
        
        # Detect if user requests Google Meet conference
        create_meet = False
        meet_keywords = ['google meet', 'meet', 'video call', 'video conference', 'online meeting', 'virtual meeting', 'conference call', 'zoom', 'online', 'remote']
        
        # Check title and description for meet keywords
        text_to_check = f"{title} {description or ''}".lower()
        create_meet = any(keyword in text_to_check for keyword in meet_keywords)
        
        # Also check recent conversation history for meet requests
        if not create_meet and self.agent:
            try:
                recent_messages = self.agent.get_conversation_history()
                if recent_messages:
                    # Check last few messages for meet-related keywords
                    recent_text = ' '.join([msg.get('content', '') for msg in recent_messages[-3:] if msg.get('content')])
                    create_meet = any(keyword in recent_text.lower() for keyword in meet_keywords)
            except:
                pass  # If history access fails, continue without it
        
        # Create appointment with user information
        return self.create_appointment(
            title=title,
            date_string=date_string,
            time_string=time_string,
            duration_minutes=duration_minutes,
            description=description,
            attendee_emails=[user_info.get('email')] if user_info.get('email') else None,
            user_name=user_info.get('name'),
            user_phone=user_info.get('phone'),
            user_email=user_info.get('email'),
            create_meet_conference=create_meet
        )

    def get_tools(self) -> List[FunctionTool]:
        """Get list of LlamaIndex FunctionTool objects."""
        return [
            FunctionTool.from_defaults(
                fn=self.check_availability,
                name="check_availability",
                description="Check calendar availability for a specific date and time duration. Use this when users ask about free time slots."
            ),
            FunctionTool.from_defaults(
                fn=self.create_appointment_with_user_info,
                name="create_appointment", 
                description="Create a new calendar appointment with user information. ONLY use this after collecting user's name AND contact info (email OR phone). This tool will automatically validate required information and send email invitations."
            ),
            FunctionTool.from_defaults(
                fn=self.list_upcoming_events,
                name="list_upcoming_events",
                description="List upcoming calendar events. Use this when users want to see their schedule or upcoming meetings."
            ),
            FunctionTool.from_defaults(
                fn=self.reschedule_appointment,
                name="reschedule_appointment",
                description="Reschedule an existing appointment to a new date/time. Use this when users want to move or change an existing meeting."
            )
        ]