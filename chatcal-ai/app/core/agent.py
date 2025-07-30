"""Main ChatCal.ai agent that combines LLM with calendar tools."""

from typing import List, Dict, Optional
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import BaseTool
from llama_index.core.memory import ChatMemoryBuffer
from app.core.llm_gemini import gemini_llm
from app.core.tools import CalendarTools
from app.personality.prompts import SYSTEM_PROMPT, GREETING_TEMPLATES, ENCOURAGEMENT_PHRASES
import random


class ChatCalAgent:
    """Main ChatCal.ai conversational agent."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.calendar_tools = CalendarTools()
        self.llm = gemini_llm.get_llm()
        
        # Set up memory
        self.memory = ChatMemoryBuffer(token_limit=3000)
        
        # Create agent with tools
        self.agent = self._create_agent()
        self.conversation_started = False
    
    def _create_agent(self) -> ReActAgent:
        """Create the ReAct agent with calendar tools."""
        # Get calendar tools
        tools = self.calendar_tools.get_tools()
        
        # Enhanced system prompt for calendar agent
        enhanced_system_prompt = f"""{SYSTEM_PROMPT}

## Calendar Assistant Capabilities

You have access to the following calendar management tools:
1. **check_availability**: Find free time slots on specific dates
2. **create_appointment**: Schedule new meetings and appointments  
3. **list_upcoming_events**: Show upcoming calendar events
4. **reschedule_appointment**: Move existing appointments to new times

## Conversation Guidelines

When users ask about scheduling:
1. **Always be enthusiastic** and use encouraging language
2. **Ask clarifying questions** if needed (duration, attendees, etc.)
3. **Suggest optimal times** based on availability
4. **Confirm details** before creating appointments
5. **Celebrate successful bookings** with positive reinforcement

## Example Interactions

User: "I need to schedule a meeting with John next week"
You: "I'd be absolutely delighted to help you schedule that meeting with John! 🌟 What day next week works best for you? And how long should I book this for - 30 minutes, an hour?"

User: "Check my availability for tomorrow"  
You: "Let me check your calendar for tomorrow! ✨ [use check_availability tool] Great news! Here's what I found..."

User: "Book me a 1-hour meeting with Sarah for Tuesday at 2pm"
You: "Perfect! Let me get that scheduled for you right away! [use create_appointment tool] Fantastic! 🎉 Your meeting with Sarah is all set..."

Always maintain your friendly, jovial personality while being helpful and efficient!"""

        # Create agent
        agent = ReActAgent.from_tools(
            tools=tools,
            llm=self.llm,
            verbose=True,
            memory=self.memory,
            system_prompt=enhanced_system_prompt,
            max_iterations=10
        )
        
        return agent
    
    def start_conversation(self) -> str:
        """Start a new conversation with greeting."""
        if not self.conversation_started:
            greeting = random.choice(GREETING_TEMPLATES)
            self.conversation_started = True
            return greeting
        return ""
    
    def chat(self, message: str) -> str:
        """Process a user message and return response."""
        try:
            # Validate input
            if not message or not message.strip():
                return "I'd love to help! Could you tell me what you need? 😊"
            
            if len(message) > 1000:
                return "That's quite a message! Could you break it down into smaller parts? I work better with shorter requests. 📝"
            
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