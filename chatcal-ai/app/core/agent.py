"""Main ChatCal.ai agent that combines LLM with calendar tools."""

from typing import List, Dict, Optional
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.tools import BaseTool
from llama_index.core.memory import ChatMemoryBuffer
from app.core.llm_anthropic import anthropic_llm
from app.core.tools import CalendarTools
from app.personality.prompts import SYSTEM_PROMPT, ENCOURAGEMENT_PHRASES
from app.config import settings
import random


class ChatCalAgent:
    """Main ChatCal.ai conversational agent."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.calendar_tools = CalendarTools(agent=self)
        self.llm = anthropic_llm.get_llm()
        
        # User information storage
        self.user_info = {
            "name": None,
            "email": None,
            "phone": None,
            "preferences": {}
        }
        
        # Meeting ID storage for cancellation tracking
        self.stored_meetings = {}
        
        # Conversation state for multi-turn operations
        self.conversation_state = {
            "pending_operation": None,  # "cancellation", "booking", etc.
            "operation_context": {},    # Context data for the pending operation
            "awaiting_clarification": False  # Whether we're waiting for user clarification
        }
        
        # Set up memory
        self.memory = ChatMemoryBuffer(token_limit=3000)
        
        # Create agent with tools
        self.agent = self._create_agent()
        self.conversation_started = False
    
    def _create_agent(self):
        """Create the ReAct agent with calendar tools."""
        # Get calendar tools 
        tools = self.calendar_tools.get_tools()
        
        # Get current user context
        user_context = self._get_user_context()
        
        # Enhanced system prompt for calendar agent with Peter's contact info
        system_prompt_with_contacts = SYSTEM_PROMPT.format(
            my_phone_number=settings.my_phone_number,
            my_email_address=settings.my_email_address
        )
        
        enhanced_system_prompt = f"""{system_prompt_with_contacts}

{user_context}

## Response Guidelines

- Be conversational and natural, like a helpful human assistant
- Keep responses concise and focused on the user's needs
- Never mention tools, capabilities, or technical details unless asked
- If user provides contact info (email/phone), remember it and use it
- Never ask for "secondary email" or additional contact if they already provided one
- If you have all required info (name + contact), book immediately without asking for confirmation
- Format responses with proper line breaks - each detail on its own line"""

        # Use direct LLM chat for now (avoiding complex agent API issues)
        # The tools will be called manually based on message analysis
        self.tools = tools
        self.system_prompt = enhanced_system_prompt
        agent = self  # Use self as the agent
        
        # Override the system prompt directly on the agent if possible
        if hasattr(agent, '_system_prompt'):
            agent._system_prompt = enhanced_system_prompt
        
        return agent
    
    def _get_user_context(self) -> str:
        """Generate user context for the system prompt."""
        missing = []
        if not self.user_info.get("name"):
            missing.append("first name")
        if not self.user_info.get("email") and not self.user_info.get("phone"):
            missing.append("contact (email or phone)")
            
        if missing:
            return f"## Missing Info: {', '.join(missing)}"
        else:
            return "## User Info: Complete - ready to book"
    
    def _get_conversation_state_context(self) -> str:
        """Generate conversation state context for the system prompt."""
        if not self.conversation_state["pending_operation"]:
            return ""
        
        if self.conversation_state["pending_operation"] == "cancellation" and self.conversation_state["awaiting_clarification"]:
            context = self.conversation_state["operation_context"]
            return f"""## Conversation State: AWAITING CANCELLATION CLARIFICATION
- User wants to cancel a meeting for: {context.get('user_name', 'unknown')}
- Original date/time info: {context.get('date_string', 'none')} {context.get('time_string', 'none')}
- Waiting for user to provide more specific time/date details
- Do NOT ask about meeting purpose - only ask for time/date clarification if needed"""
        
        return ""
    
    def _process_message_with_llm(self, message: str) -> str:
        """Process message using direct LLM calls with manual tool invocation."""
        try:
            print(f"🔍 Debug - Processing message with LLM: '{message[:50]}...'")
            # Check if we need to call any tools based on the message
            tool_result = self._check_and_call_tools(message)
            print(f"🔍 Debug - Tool result: '{tool_result[:50] if tool_result else 'None'}...')")
            
            # Create enhanced message with tool results if any
            enhanced_message = message
            if tool_result:
                enhanced_message = f"[Tool Result: {tool_result}]\n\nUser: {message}"
            
            # Add user message to memory
            user_message = ChatMessage(role=MessageRole.USER, content=enhanced_message)
            self.memory.put(user_message)
            
            # Build conversation history for LLM with updated user context
            current_user_context = self._get_user_context()
            conversation_state_context = self._get_conversation_state_context()
            
            current_system_prompt = f"""{self.system_prompt.split('## Missing Info:')[0].split('## User Info:')[0].rstrip()}

{current_user_context}

{conversation_state_context}

## Response Guidelines

- Be conversational and natural, like a helpful human assistant
- Keep responses concise and focused on the user's needs
- Never mention tools, capabilities, or technical details unless asked
- If user provides contact info (email/phone), remember it and use it
- Never ask for "secondary email" or additional contact if they already provided one
- If you have all required info (name + contact), book immediately without asking for confirmation
- Format responses with proper line breaks - each detail on its own line"""
            
            messages = [ChatMessage(role=MessageRole.SYSTEM, content=current_system_prompt)]
            
            # Add conversation history from memory
            history_messages = self.memory.get_all()
            messages.extend(history_messages)
            
            # Get LLM response
            response = self.llm.chat(messages)
            response_text = response.message.content
            
            # Add assistant response to memory
            assistant_message = ChatMessage(role=MessageRole.ASSISTANT, content=response_text)
            self.memory.put(assistant_message)
            
            return response_text
            
        except Exception as e:
            print(f"LLM processing error: {e}")
            import traceback
            traceback.print_exc()
            return "I'm having trouble processing your request right now. Could you try again?"
    
    def _check_and_call_tools(self, message: str) -> str:
        """Check if message requires tool calls and execute them."""
        import re
        
        # Check for booking requests
        booking_patterns = [
            r"schedule|book|appointment|meeting",
            r"available|availability|free time",
            r"reschedule|move|change",
            r"cancel|delete|remove"
        ]
        
        message_lower = message.lower()
        print(f"🔍 Debug - Checking tools for message: '{message[:50]}...'")
        print(f"🔍 Debug - User info complete: {self.has_complete_user_info()}")
        print(f"🔍 Debug - User info: {self.user_info}")
        
        # Check availability requests
        if any(word in message_lower for word in ["available", "availability", "free", "open"]):
            # Extract date from message (basic pattern matching)
            date_patterns = [
                r"tomorrow",
                r"today", 
                r"monday|tuesday|wednesday|thursday|friday|saturday|sunday",
                r"\d{1,2}/\d{1,2}",
                r"next week",
                r"this week"
            ]
            
            date_found = None
            for pattern in date_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    date_found = match.group()
                    break
            
            if date_found:
                try:
                    # Call availability tool
                    availability_tool = None
                    for tool in self.tools:
                        if "availability" in tool.metadata.name.lower():
                            availability_tool = tool
                            break
                    
                    if availability_tool:
                        result = availability_tool.call(date=date_found)
                        return f"Availability check result: {result}"
                except Exception as e:
                    return f"Could not check availability: {str(e)}"
        
        # Check for booking requests with complete info
        booking_keywords = ["schedule", "book", "appointment", "meeting"]
        has_booking_keyword = any(word in message_lower for word in booking_keywords)
        print(f"🔍 Debug - Has booking keyword: {has_booking_keyword}")
        print(f"🔍 Debug - Booking keywords found: {[word for word in booking_keywords if word in message_lower]}")
        
        if self.has_complete_user_info() and has_booking_keyword:
            try:
                print(f"🔧 Processing booking request from {self.user_info['name']}: '{message}'")
                
                # Extract meeting details from message
                duration = self._extract_duration(message_lower)  # Extract duration
                meeting_type = self._extract_meeting_type(message_lower)  # Extract meeting type
                
                # Extract date and time from message
                date_found = self._extract_date(message_lower)
                time_found = self._extract_time(message_lower)
                
                print(f"📅 Extracted - Date: {date_found}, Time: {time_found}, Duration: {duration}, Type: {meeting_type}")
                
                # If we found both date and time, proceed with booking
                if date_found and time_found:
                    # Find the create appointment tool
                    create_tool = None
                    for tool in self.tools:
                        if "create_appointment" == tool.metadata.name:
                            create_tool = tool
                            break
                    
                    if create_tool:
                        # Create title based on meeting type
                        title = f"{duration}-minute {meeting_type} with Peter Michael Gits"
                        
                        print(f"🔧 Calling create_appointment tool with: title='{title}', date='{date_found}', time='{time_found}', duration={duration}")
                        
                        # Call the tool with correct parameters
                        result = create_tool.fn(
                            title=title,
                            date_string=date_found,
                            time_string=time_found,
                            duration_minutes=duration,
                            description=f"Meeting with {self.user_info['name']}"
                        )
                        
                        print(f"✅ Tool result: {result[:100]}...")
                        return result
                    else:
                        print("❌ Could not find create_appointment tool")
                        return "I'm having trouble accessing the calendar system right now. Please try again in a moment."
                else:
                    print(f"⚠️ Missing booking details - Date: {date_found}, Time: {time_found}")
                    # If date/time not found, let the LLM handle the conversation naturally
                    return ""
                    
            except Exception as e:
                print(f"❌ Booking error: {e}")
                return f"I encountered an issue while trying to book your appointment: {str(e)}"
        
        # First check if we're continuing a cancellation conversation
        if self.conversation_state["pending_operation"] == "cancellation" and self.conversation_state["awaiting_clarification"]:
            # User is providing clarification for a pending cancellation
            context = self.conversation_state["operation_context"]
            print(f"🔄 Processing cancellation clarification from {context.get('user_name')}: '{message}'")
            
            # Extract time/date information from the clarification
            time_patterns = [
                r"\d{1,2}:\d{2}\s*(?:am|pm)",
                r"\d{1,2}\s*(?:am|pm)",
                r"morning|afternoon|evening|noon"
            ]
            
            date_patterns = [
                r"tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday",
                r"\d{1,2}/\d{1,2}",
                r"next week|this week"
            ]
            
            # Look for additional time/date info in the clarification
            additional_time = None
            additional_date = None
            
            for pattern in time_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    additional_time = match.group()
                    break
            
            for pattern in date_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    additional_date = match.group()
                    break
            
            # Use the clarification to complete the cancellation
            try:
                cancel_tool = None
                for tool in self.tools:
                    if "cancel" in tool.metadata.name.lower() and "details" in tool.metadata.name.lower():
                        cancel_tool = tool
                        break
                
                if cancel_tool:
                    # Use stored context plus any new info from clarification
                    final_date = additional_date or context.get("date_string", "")
                    final_time = additional_time or context.get("time_string", "")
                    
                    result = cancel_tool.call(
                        user_name=context["user_name"],
                        date_string=final_date,
                        time_string=final_time
                    )
                    
                    # Clear the conversation state
                    self.conversation_state = {
                        "pending_operation": None,
                        "operation_context": {},
                        "awaiting_clarification": False
                    }
                    print(f"✅ Cleared conversation state after successful cancellation")
                    
                    return result
            except Exception as e:
                # Clear state on error
                self.conversation_state = {
                    "pending_operation": None,
                    "operation_context": {},
                    "awaiting_clarification": False
                }
                print(f"❌ Cleared conversation state after cancellation error: {str(e)}")
                return f"Could not cancel meeting: {str(e)}"
        
        # Check for numbered cancellation requests (e.g., "cancel #1", "cancel the first one")
        elif any(word in message_lower for word in ["cancel", "delete", "remove"]):
            # Look for number indicators
            number_patterns = [
                r"#(\d+)", r"number (\d+)", r"(\d+)(?:st|nd|rd|th)?",
                r"first", r"second", r"third", r"fourth", r"fifth"
            ]
            
            number_words = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5}
            selected_number = None
            
            for pattern in number_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    if match.group().strip() in number_words:
                        selected_number = number_words[match.group().strip()]
                    else:
                        try:
                            selected_number = int(match.group(1) if match.groups() else match.group().strip("#"))
                        except:
                            continue
                    break
            
            # If user selected a number and we have their stored meetings info, try to cancel by selection
            if selected_number and self.user_info.get('name'):
                # Find their meetings to get the selected one
                try:
                    find_tool = None
                    for tool in self.tools:
                        if "find_user_meetings" in tool.metadata.name.lower():
                            find_tool = tool
                            break
                    
                    if find_tool:
                        # This is a bit of a workaround - we'll get their meetings and extract the nth one
                        from datetime import datetime, timedelta
                        now = datetime.now(self.calendar_tools.calendar_service.default_timezone)
                        search_end = now + timedelta(days=30)
                        
                        events = self.calendar_tools.calendar_service.list_events(
                            time_min=now,
                            time_max=search_end,
                            max_results=50
                        )
                        
                        # Find meetings that match the user name
                        matching_events = []
                        for event in events:
                            event_summary = event.get('summary', '').lower()
                            event_description = event.get('description', '').lower()
                            
                            if (self.user_info['name'].lower() in event_summary or 
                                self.user_info['name'].lower() in event_description or
                                f"meeting with {self.user_info['name'].lower()}" in event_summary):
                                matching_events.append(event)
                        
                        if matching_events and 1 <= selected_number <= len(matching_events):
                            # Cancel the selected meeting
                            selected_event = matching_events[selected_number - 1]
                            google_meeting_id = selected_event.get('id')
                            
                            # Try to find custom meeting ID
                            custom_meeting_id = None
                            if self.agent:
                                stored_meetings = self.agent.get_stored_meetings()
                                for stored_id, info in stored_meetings.items():
                                    if info.get('google_id') == google_meeting_id:
                                        custom_meeting_id = stored_id
                                        break
                            
                            # Cancel using the meeting ID
                            cancel_tool = None
                            for tool in self.tools:
                                if "cancel" in tool.metadata.name.lower() and "id" in tool.metadata.name.lower():
                                    cancel_tool = tool
                                    break
                            
                            if cancel_tool:
                                if custom_meeting_id:
                                    result = cancel_tool.call(meeting_id=custom_meeting_id)
                                else:
                                    # Fall back to Google ID
                                    result = cancel_tool.call(meeting_id=google_meeting_id)
                                return result
                        else:
                            return f"I couldn't find meeting #{selected_number}. Please check the list and try again."
                            
                except Exception as e:
                    return f"Could not cancel meeting: {str(e)}"
        
        # Check for new cancellation requests
        elif any(word in message_lower for word in ["cancel", "delete", "remove"]) and any(word in message_lower for word in ["meeting", "appointment"]):
            # Look for meeting ID in message first
            meeting_id_pattern = r"\b\d{4}-\d{4}-\d+m\b"  # Our custom format: MMDD-HHMM-DURm
            meeting_ids = re.findall(meeting_id_pattern, message)
            
            if meeting_ids:
                # Try to cancel by custom meeting ID
                try:
                    cancel_tool = None
                    for tool in self.tools:
                        if "cancel" in tool.metadata.name.lower() and "id" in tool.metadata.name.lower():
                            cancel_tool = tool
                            break
                    
                    if cancel_tool:
                        result = cancel_tool.call(meeting_id=meeting_ids[0])
                        return result  # Return direct result (already formatted HTML)
                except Exception as e:
                    return f"Could not cancel meeting: {str(e)}"
            else:
                # Try to cancel by user name and date (never ask about purpose)
                if self.user_info.get('name'):
                    try:
                        # Extract date from message
                        date_patterns = [
                            r"tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday",
                            r"\d{1,2}/\d{1,2}",
                            r"next week|this week|friday|monday|tuesday|wednesday|thursday"
                        ]
                        
                        # Extract time from message
                        time_patterns = [
                            r"\d{1,2}:\d{2}\s*(?:am|pm)",
                            r"\d{1,2}\s*(?:am|pm)",
                            r"morning|afternoon|evening|noon"
                        ]
                        
                        date_found = None
                        time_found = None
                        
                        for pattern in date_patterns:
                            match = re.search(pattern, message_lower)
                            if match:
                                date_found = match.group()
                                break
                        
                        for pattern in time_patterns:
                            match = re.search(pattern, message_lower)
                            if match:
                                time_found = match.group()
                                break
                        
                        # Check if user indicates they don't remember the time
                        no_time_indicators = [
                            "don't remember", "can't remember", "forgot", "not sure when",
                            "don't know when", "what time", "which one", "don't recall"
                        ]
                        
                        user_doesnt_remember = any(indicator in message_lower for indicator in no_time_indicators)
                        
                        if date_found and not user_doesnt_remember:
                            # User provided specific date/time - use details cancellation
                            cancel_tool = None
                            for tool in self.tools:
                                if "cancel" in tool.metadata.name.lower() and "details" in tool.metadata.name.lower():
                                    cancel_tool = tool
                                    break
                            
                            if cancel_tool:
                                result = cancel_tool.call(
                                    user_name=self.user_info['name'],
                                    date_string=date_found,
                                    time_string=time_found
                                )
                                
                                # Check if the result is asking for clarification
                                if "Found multiple meetings" in result or "Can you be more specific" in result:
                                    # Store the cancellation context
                                    self.conversation_state = {
                                        "pending_operation": "cancellation",
                                        "operation_context": {
                                            "user_name": self.user_info['name'],
                                            "date_string": date_found,
                                            "time_string": time_found,
                                            "original_message": message
                                        },
                                        "awaiting_clarification": True
                                    }
                                    print(f"🔄 Set conversation state: awaiting cancellation clarification for {self.user_info['name']}")
                                
                                return result  # Return direct result (already formatted HTML)
                        else:
                            # User doesn't remember time or didn't provide date - show all their meetings
                            find_tool = None
                            for tool in self.tools:
                                if "find_user_meetings" in tool.metadata.name.lower():
                                    find_tool = tool
                                    break
                            
                            if find_tool:
                                result = find_tool.call(user_name=self.user_info['name'])
                                return result  # Return list of meetings for user to choose
                    except Exception as e:
                        return f"Could not cancel meeting: {str(e)}"
        
        return ""
    
    def _extract_date(self, message_lower: str) -> str:
        """Extract date from message."""
        import re
        
        date_patterns = [
            (r"tomorrow", "tomorrow"),
            (r"today", "today"),
            (r"monday|tuesday|wednesday|thursday|friday|saturday|sunday", None),
            (r"next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", None),
            (r"this\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", None),
            (r"\d{1,2}/\d{1,2}/\d{2,4}", None),
            (r"\d{1,2}/\d{1,2}", None),
            (r"next week", "next week"),
            (r"this week", "this week")
        ]
        
        for pattern, default_value in date_patterns:
            match = re.search(pattern, message_lower)
            if match:
                return default_value or match.group()
        
        return None
    
    def _extract_time(self, message_lower: str) -> str:
        """Extract time from message."""
        import re
        
        time_patterns = [
            r"\d{1,2}:\d{2}\s*(?:am|pm)",
            r"\d{1,2}\s*(?:am|pm)",
            r"\d{1,2}:\d{2}",
            r"morning|afternoon|evening|noon"
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, message_lower)
            if match:
                time_str = match.group()
                # Normalize common time formats
                if time_str == "morning":
                    return "9:00 AM"
                elif time_str == "afternoon":
                    return "2:00 PM"
                elif time_str == "evening":
                    return "6:00 PM"
                elif time_str == "noon":
                    return "12:00 PM"
                return time_str
        
        return None
    
    def _extract_duration(self, message_lower: str) -> int:
        """Extract duration from message in minutes."""
        import re
        
        # Look for explicit duration mentions
        duration_patterns = [
            (r"(\d+)\s*-?\s*minute", lambda m: int(m.group(1))),
            (r"(\d+)\s*-?\s*min", lambda m: int(m.group(1))),
            (r"(\d+)\s*hour", lambda m: int(m.group(1)) * 60),
            (r"(\d+)\s*hr", lambda m: int(m.group(1)) * 60),
            (r"half\s*hour", lambda m: 30),
            (r"(\d+)\s*and\s*a\s*half\s*hour", lambda m: int(m.group(1)) * 60 + 30)
        ]
        
        for pattern, converter in duration_patterns:
            match = re.search(pattern, message_lower)
            if match:
                return converter(match)
        
        # Default durations based on meeting type
        if any(word in message_lower for word in ["consultation", "advisory", "meeting"]):
            return 60
        elif any(word in message_lower for word in ["brief", "quick", "short"]):
            return 30
        else:
            return 60  # Default to 1 hour
    
    def _extract_meeting_type(self, message_lower: str) -> str:
        """Extract meeting type from message."""
        # Check for Google Meet/video keywords
        if any(word in message_lower for word in ["google meet", "meet", "video call", "video conference", "online meeting", "virtual", "remote"]):
            if any(word in message_lower for word in ["consultation", "advisory"]):
                return "Google Meet Consultation"
            else:
                return "Google Meet Meeting"
        
        # Check for specific meeting types
        if "consultation" in message_lower:
            return "Consultation"
        elif "advisory" in message_lower:
            return "Advisory Session"
        elif "project" in message_lower:
            return "Project Meeting"
        else:
            return "Meeting"
    
    def update_user_info(self, info_type: str, value: str) -> bool:
        """Update user information."""
        if info_type in self.user_info:
            self.user_info[info_type] = value
            return True
        return False
    
    def get_user_info(self) -> Dict:
        """Get current user information."""
        return self.user_info.copy()
    
    def has_complete_user_info(self) -> bool:
        """Check if minimum required user information is collected (name + at least one contact)."""
        has_name = bool(self.user_info.get("name"))
        has_contact = bool(self.user_info.get("email") or self.user_info.get("phone"))
        return has_name and has_contact
    
    def has_ideal_user_info(self) -> bool:
        """Check if all preferred user information is collected (name + both contacts)."""
        return all([
            self.user_info.get("name"),
            self.user_info.get("email"), 
            self.user_info.get("phone")
        ])
    
    def get_missing_user_info(self) -> List[str]:
        """Get list of missing required user information."""
        missing = []
        if not self.user_info.get("name"):
            missing.append("name")
        
        # For contacts, only mark as missing if we have neither
        if not self.user_info.get("email") and not self.user_info.get("phone"):
            missing.append("contact (email OR phone)")
        
        return missing
    
    def get_missing_ideal_info(self) -> List[str]:
        """Get list of missing information for ideal collection (both contacts)."""
        missing = []
        if not self.user_info.get("name"):
            missing.append("name")
        if not self.user_info.get("email"):
            missing.append("email")
        if not self.user_info.get("phone"):
            missing.append("phone")
        return missing
    
    def extract_user_info_from_message(self, message: str) -> Dict:
        """Extract user information from user messages using simple patterns."""
        import re
        extracted = {}
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, message)
        if emails:
            extracted['email'] = emails[0]
        
        # Phone pattern (multiple formats including "call me at 630 880 5488")
        phone_patterns = [
            r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',  # Standard format
            r'call me at\s*(\d{3})[-.\s]*(\d{3})[-.\s]*(\d{4})',  # "call me at" format
            r'phone\s*:?\s*(\d{3})[-.\s]*(\d{3})[-.\s]*(\d{4})',  # "phone:" format
            r'(\d{3})[-.\s]+(\d{3})[-.\s]+(\d{4})'  # Simple space/dash separated
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                match = matches[0]
                if isinstance(match, tuple):
                    # Join all non-empty parts
                    phone_digits = ''.join([part for part in match if part])
                    if len(phone_digits) >= 10:  # Valid phone number
                        extracted['phone'] = phone_digits
                        break
        
        # Name pattern (various formats)
        name_patterns = [
            r"my name is ([A-Za-z\s]{2,30})",
            r"i'm ([A-Za-z\s]{2,30})",
            r"this is ([A-Za-z\s]{2,30})",
            r"i am ([A-Za-z\s]{2,30})",
            r"(?:^|\s)([A-Z][a-z]+(?:\s[A-Z][a-z]+)*),?\s+(?:here|speaking|calling)"  # "Betty, here" or "John Smith calling"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, message.lower())
            if match:
                potential_name = match.group(1).strip().title()
                # Simple validation - name should be 2-50 chars and not contain numbers
                if 2 <= len(potential_name) <= 50 and not any(char.isdigit() for char in potential_name):
                    extracted['name'] = potential_name
                    break
        
        return extracted
    
    def start_conversation(self) -> str:
        """Start a new conversation."""
        if not self.conversation_started:
            self.conversation_started = True
        return ""
    
    def chat(self, message: str) -> str:
        """Process a user message and return response."""
        import re  # Import re module for regex operations
        
        try:
            # Validate input
            if not message or not message.strip():
                return "I'd love to help! Could you tell me what you need? 😊"
            
            if len(message) > 1000:
                return "That's quite a message! Could you break it down into smaller parts? I work better with shorter requests. 📝"
            
            # Check for explicit contact information requests (not booking requests)
            contact_request_patterns = [
                r"what.{0,20}peter.{0,20}(phone|number|contact)",
                r"(phone|number|contact).{0,20}peter",
                r"how.{0,20}(reach|contact).{0,20}peter",
                r"peter.{0,20}(email|phone).{0,20}address"
            ]
            
            is_contact_request = any(re.search(pattern, message.lower()) for pattern in contact_request_patterns)
            is_booking_request = any(word in message.lower() for word in ['book', 'schedule', 'appointment', 'meeting', 'available', 'time'])
            
            if is_contact_request and not is_booking_request:
                contact_response = f"Peter's contact information:\n📞 Phone: {settings.my_phone_number}\n📧 Email: {settings.my_email_address}\n\nI can also help you schedule an appointment with Peter through this chat. What would you prefer?"
                return contact_response
            
            # Extract and store user information from the message
            extracted_info = self.extract_user_info_from_message(message)
            for info_type, value in extracted_info.items():
                if not self.user_info.get(info_type):  # Only update if we don't already have this info
                    self.update_user_info(info_type, value)
                    print(f"📝 Extracted {info_type}: {value}")
            
            # Debug: Show current user info status
            if extracted_info:
                print(f"👤 Current user info: {self.user_info}")
            
            # Start conversation if needed
            if not self.conversation_started:
                self.start_conversation()
            
            print(f"🔍 Debug - About to call _process_message_with_llm")
            # Regular chat interaction using direct LLM
            result = self._process_message_with_llm(message)
            print(f"🔍 Debug - Result from _process_message_with_llm: '{result[:100] if result else 'None'}...'")
            return result
            
        except Exception as e:
            print(f"⚠️ Agent error: {e}")
            # Friendly error handling with different messages based on error type
            if "rate limit" in str(e).lower():
                return "Whoa there! I'm getting a bit overwhelmed. Could you wait just a moment and try again? ⏱️"
            elif "authentication" in str(e).lower():
                return "I'm having trouble connecting to your calendar. Could you check if I'm properly authenticated? 🔐"
            elif "network" in str(e).lower() or "connection" in str(e).lower():
                return "I'm having connectivity issues right now. Let's try that again in a moment! 🌐"
            else:
                error_phrases = [
                    "Oops! I'm having a tiny technical hiccup. Could you try that again? 😊",
                    "Oh dear! Something went a bit wonky on my end. Let's give that another shot! 🔧",
                    "Hmm, I'm having a moment here! Could you repeat that for me? 💫"
                ]
                return random.choice(error_phrases)
    
    def stream_chat(self, message: str):
        """Stream a chat response (generator)."""
        try:
            # Validate input
            if not message or not message.strip():
                error_message = "I'd love to help! Could you tell me what you need? 😊"
                for word in error_message.split():
                    yield word + " "
                return
            
            if len(message) > 1000:
                error_message = "That's quite a message! Could you break it down into smaller parts? 📝"
                for word in error_message.split():
                    yield word + " "
                return
            
            # Extract and store user information from the message
            extracted_info = self.extract_user_info_from_message(message)
            for info_type, value in extracted_info.items():
                if not self.user_info.get(info_type):  # Only update if we don't already have this info
                    self.update_user_info(info_type, value)
            
            # Start conversation if needed
            if not self.conversation_started:
                self.start_conversation()
            
            # Stream the response using direct LLM
            agent_response = self._process_message_with_llm(message)
                
            # Yield the response word by word to simulate streaming
            for word in agent_response.split():
                yield word + " "
                
        except Exception as e:
            print(f"⚠️ Stream chat error: {e}")
            if "rate limit" in str(e).lower():
                error_message = "I'm getting a bit overwhelmed. Let's try again in a moment! ⏱️"
            elif "authentication" in str(e).lower():
                error_message = "Having calendar connection issues. Please check authentication! 🔐"
            else:
                error_message = "I'm having a bit of trouble right now. Could you try again? 😊"
            
            for word in error_message.split():
                yield word + " "
    
    def reset_conversation(self):
        """Reset the conversation memory."""
        self.memory.reset()
        self.conversation_started = False
    
    def get_conversation_history(self) -> List[Dict]:
        """Get the conversation history."""
        messages = self.memory.get_all()
        return [
            {
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": getattr(msg, 'timestamp', None)
            }
            for msg in messages
        ]
    
    def add_context(self, context: str):
        """Add context information to the conversation."""
        context_message = f"[Context: {context}]"
        # Add as system message to memory if needed
        
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return [tool.metadata.name for tool in self.calendar_tools.get_tools()]
    
    def handle_special_commands(self, message: str) -> Optional[str]:
        """Handle special commands like /help, /schedule, etc."""
        message = message.lower().strip()
        
        if message in ['/help', 'help', 'what can you do']:
            return """I'm ChatCal, Peter Michael Gits' scheduling assistant! 📅 Here's how I can help you:

🤝 **Book a consultation with Peter**: "I'd like to schedule a business consultation"
💼 **Schedule a meeting**: "I need a 30-minute meeting with Peter next week"
📊 **Project discussions**: "Book time to discuss my project with Peter"
🎯 **Advisory sessions**: "I need a 90-minute advisory session"

Meeting types available:
• **Quick chat** (30 minutes) - Brief discussions
• **Consultation** (60 minutes) - Business consultations
• **Project meeting** (60 minutes) - Project planning/review
• **Advisory session** (90 minutes) - Extended strategic sessions

Peter typically meets between 9 AM and 5 PM. Just tell me what you'd like to discuss and when you're available!"""
        
        elif message in ['/status', 'status']:
            available_tools = self.get_available_tools()
            auth_status = "✅ Connected" if self.calendar_tools.calendar_service.auth.is_authenticated() else "❌ Not authenticated"
            
            return f"""📊 **ChatCal Status**
Calendar Connection: {auth_status}
Available Tools: {len(available_tools)}
Session ID: {self.session_id}
Tools: {', '.join(available_tools)}

Ready to help you manage your calendar! 🚀"""
        
        return None
    
    def store_meeting_id(self, meeting_id: str, meeting_info: dict):
        """Store meeting ID and info for cancellation tracking."""
        self.stored_meetings[meeting_id] = meeting_info
    
    def get_stored_meetings(self) -> dict:
        """Get all stored meeting IDs and info."""
        return self.stored_meetings.copy()
    
    def remove_stored_meeting(self, meeting_id: str):
        """Remove a stored meeting ID."""
        if meeting_id in self.stored_meetings:
            del self.stored_meetings[meeting_id]