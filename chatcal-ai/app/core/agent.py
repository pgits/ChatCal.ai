"""Main ChatCal.ai agent that combines LLM with calendar tools."""

from typing import List, Dict, Optional
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import BaseTool
from llama_index.core.memory import ChatMemoryBuffer
from app.core.llm_anthropic import anthropic_llm
from app.core.tools import CalendarTools
from app.personality.prompts import SYSTEM_PROMPT, GREETING_TEMPLATES, ENCOURAGEMENT_PHRASES
from app.config import settings
import random


class ChatCalAgent:
    """Main ChatCal.ai conversational agent."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.calendar_tools = CalendarTools()
        self.llm = anthropic_llm.get_llm()
        
        # User information storage
        self.user_info = {
            "name": None,
            "email": None,
            "phone": None,
            "preferences": {}
        }
        
        # Set up memory
        self.memory = ChatMemoryBuffer(token_limit=3000)
        
        # Create agent with tools
        self.agent = self._create_agent()
        self.conversation_started = False
    
    def _create_agent(self) -> ReActAgent:
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

## Calendar Assistant Capabilities

You have access to the following calendar management tools:
1. **check_availability**: Find free time slots on specific dates
2. **create_appointment**: Schedule new meetings and appointments  
3. **list_upcoming_events**: Show upcoming calendar events
4. **reschedule_appointment**: Move existing appointments to new times

## User Information Guidelines

- ALWAYS collect user information early: full name, email, phone number
- Store and remember this information throughout the conversation
- Use the user's name once you know it
- When showing availability, present times in a clear, selectable format
- Before booking, confirm all details including user contact information

## Availability Requests Recognition

Recognize these patterns as availability requests and ALWAYS use the check_availability tool:
- "What times does Peter have free [date]?"
- "What's Peter's availability for [date]?"
- "Show me Peter's open slots [date]"
- "When is Peter available [date]?"
- "Check Peter's schedule for [date]"
- "What times are available [date]?"

## Example Availability Response

When user asks "What times does Peter have free tomorrow?":
1. Use check_availability tool with date="tomorrow"
2. Format response like: "Here are Peter's available time slots for tomorrow:
• 9:00 AM - 10:00 AM
• 11:30 AM - 12:30 PM  
• 2:00 PM - 3:00 PM
• 4:00 PM - 5:00 PM

Which time would work best for you, [user's name]?"

## Example Interactions

User: "I need to schedule a meeting with Peter next week"
You: "I'd be happy to help you schedule time with Peter! First, may I have your full name for the appointment?"

User: "What times does Peter have free tomorrow?"
You: [Use check_availability tool] "Here are Peter's available times for tomorrow: [list times]"

User: "My name is John Smith, email john@example.com"
You: "Thank you, John! I have your information. Now, what type of meeting would you like to schedule with Peter?"

Always maintain your professional yet friendly personality while collecting complete user information!"""

        # Create agent with explicit system prompt
        agent = ReActAgent.from_tools(
            tools=tools,
            llm=self.llm,
            verbose=True,
            memory=self.memory,
            system_prompt=enhanced_system_prompt,
            max_iterations=10
        )
        
        # Override the system prompt directly on the agent if possible
        if hasattr(agent, '_system_prompt'):
            agent._system_prompt = enhanced_system_prompt
        
        return agent
    
    def _get_user_context(self) -> str:
        """Generate user context for the system prompt."""
        if not any(self.user_info.values()):
            return f"## Current User Information\n🚫 NO USER INFORMATION COLLECTED YET - REQUIRED BEFORE BOOKING\nYou MUST collect name AND at least one contact method (email OR phone) before any appointment booking.\n💡 Alternative: Offer Peter's direct number {settings.my_phone_number} or email {settings.my_email_address}\n⛔ DO NOT USE create_appointment TOOL WITHOUT CONTACT INFO ⛔"
        
        context = "## Current User Information\n"
        if self.user_info["name"]:
            context += f"- ✅ Name: {self.user_info['name']}\n"
        if self.user_info["email"]:
            context += f"- ✅ Email: {self.user_info['email']}\n"
        if self.user_info["phone"]:
            context += f"- ✅ Phone: {self.user_info['phone']}\n"
            
        # Check what's missing
        missing_name = not self.user_info["name"]
        missing_contact = not self.user_info["email"] and not self.user_info["phone"]
        
        if missing_name or missing_contact:
            context += "\n🚫 MISSING REQUIRED INFO: "
            missing_items = []
            if missing_name:
                missing_items.append("NAME")
            if missing_contact:
                missing_items.append("CONTACT (email OR phone)")
            context += ", ".join(missing_items) + "\n"
            
            if missing_contact:
                context += f"💡 ALTERNATIVES: Offer Peter's direct number {settings.my_phone_number} or email {settings.my_email_address}\n"
            context += "🚫🚫 ABSOLUTELY DO NOT USE create_appointment TOOL UNTIL REQUIRED INFO IS COLLECTED! 🚫🚫\n"
            context += "⛔ BOOKING IS FORBIDDEN WITHOUT CONTACT INFORMATION ⛔\n"
        else:
            # Check if we have both contacts (preferred) or just one
            if self.user_info["email"] and self.user_info["phone"]:
                context += "\n✅ ALL INFORMATION COLLECTED (Name + Both Contacts) - Ready to book appointments\n"
            else:
                contact_type = "email" if self.user_info["email"] else "phone"
                context += f"\n✅ REQUIRED INFORMATION COLLECTED (Name + {contact_type}) - Ready to book appointments\n"
                context += "💡 Consider asking for additional contact method for better communication\n"
            
        return context
    
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
        """Start a new conversation with greeting."""
        if not self.conversation_started:
            greeting = random.choice(GREETING_TEMPLATES)
            self.conversation_started = True
            return greeting
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
            
            # Start conversation if needed
            if not self.conversation_started:
                greeting = self.start_conversation()
                # For the first message, respond with greeting + handling the message
                response = self.agent.chat(message)
                return f"{greeting}\n\n{response.response}"
            
            # Regular chat interaction
            response = self.agent.chat(message)
            return response.response
            
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
                greeting = self.start_conversation()
                # Yield greeting first
                for word in greeting.split():
                    yield word + " "
                yield "\n\n"
            
            # Stream the response
            response = self.agent.stream_chat(message)
            for token in response.response_gen:
                yield token
                
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