# ChatCal.ai Architecture Overview

## System Architecture

ChatCal.ai v3.0 is built as a production-ready microservices architecture with the following components:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                           │
├─────────────────────────────────────────────────────────────────┤
│  Chat Widget        │  Simple Chat     │  Embeddable Widget    │
│  (Premium UI)       │  (Development)   │  (Third-party Sites)  │
└─────────────────────┴──────────────────┴───────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway Layer                        │
├─────────────────────────────────────────────────────────────────┤
│              FastAPI with async request handling               │
│         POST /chat │ GET /health │ OAuth endpoints             │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                      Core Agent Layer                          │
├─────────────────────────────────────────────────────────────────┤
│  Conversation Agent │ Memory Buffer │ Tool Invocation System   │
│  (LlamaIndex)       │ (Redis-based) │ (Calendar + Email)       │
└─────────────────────┴───────────────┴─────────────────────────────┘
                                │
┌─────────────────┬───────────────────┬─────────────────────────────┐
│   LLM Services  │  Calendar Service │    Email Service            │
├─────────────────┼───────────────────┼─────────────────────────────┤
│  Groq Primary   │  Google Calendar  │  Gmail SMTP                 │
│  Anthropic      │  OAuth2 + API     │  Professional Templates     │
│  Fallback       │  Meeting Creation │  Dual Recipients (.ics)     │
└─────────────────┴───────────────────┴─────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                     Infrastructure Layer                        │
├─────────────────────────────────────────────────────────────────┤
│    Redis Session Store │ Docker Containers │ Health Monitoring  │
│    Persistent Memory   │ Production Ready  │ Error Handling     │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Frontend Layer

#### Chat Widget (`/chat-widget`)
- **Purpose**: Premium user interface for production deployments
- **Features**: 
  - Modern gradient design with professional styling
  - Quick action buttons (Google Meet, availability check)
  - Rich HTML response rendering
  - Responsive design for all devices
  - Embeddable in third-party websites

#### Simple Chat (`/simple-chat`)
- **Purpose**: Development and testing interface
- **Features**:
  - Fast, lightweight design
  - Full booking functionality
  - Text-focused interactions
  - Debugging-friendly output

### 2. API Gateway (FastAPI)

```python
# Key endpoints
POST /chat              # Main conversation endpoint
GET /health            # System health check
GET /simple-chat       # Development interface
GET /chat-widget       # Production interface
POST /sessions         # Session management
GET /auth/login        # Google OAuth initiation
GET /auth/callback     # OAuth callback handler
```

**Features**:
- Async request handling for high performance
- Session management with Redis
- HTML response formatting
- Error handling and logging
- CORS configuration for cross-origin requests

### 3. Core Agent System

#### Conversation Agent (`app/core/agent.py`)
The heart of ChatCal.ai with sophisticated conversation management:

```python
class ChatCalAgent:
    def __init__(self):
        self.llm = self._initialize_llm()  # Groq primary, Anthropic fallback
        self.memory = ChatMemoryBuffer()   # Persistent conversation context
        self.tools = self._load_tools()    # Calendar and email tools
        
    def process_message(self, message: str, session_id: str):
        # 1. Load conversation context from Redis
        # 2. Process message with LLM
        # 3. Check for tool invocation needs
        # 4. Execute calendar/email tools if needed
        # 5. Format response with HTML
        # 6. Save updated context to Redis
```

**Key Capabilities**:
- **Multi-turn Conversations**: Maintains context across interactions
- **Tool Invocation**: Automatically calls calendar/email functions
- **Natural Language Processing**: Extracts dates, times, durations
- **HTML Response Formatting**: Professional output styling
- **Error Recovery**: Graceful handling of failures

#### Memory System
- **Technology**: Redis-backed ChatMemoryBuffer
- **Persistence**: Conversations survive application restarts
- **Context Window**: Configurable message history limit
- **User Data**: Retains name, email, phone across sessions

### 4. LLM Integration Layer

#### Primary LLM: Groq (Llama-3.1-8b-instant)
```python
# High-performance configuration
groq_llm = Groq(
    model="llama-3.1-8b-instant",
    api_key=config.groq_api_key,
    temperature=0.1,  # Consistent responses
    max_tokens=500,   # Concise but complete
)
```

**Benefits**:
- **Speed**: 10x faster than traditional models
- **Cost**: Extremely cost-effective for production
- **Quality**: Maintains conversation intelligence
- **Reliability**: High availability and uptime

#### Fallback System
```python
def _initialize_llm(self):
    try:
        return Groq(...)  # Primary
    except Exception:
        try:
            return Anthropic(...)  # Fallback
        except Exception:
            return MockLLM(...)  # Development fallback
```

### 5. Tool System

#### Calendar Integration (`app/core/tools.py`)
```python
@tool
def create_appointment(
    title: str,
    date_string: str, 
    time_string: str,
    duration_minutes: int,
    description: str
) -> str:
    # 1. Parse natural language date/time
    # 2. Create Google Calendar event
    # 3. Generate Google Meet link
    # 4. Send email invitations
    # 5. Return confirmation with meeting ID
```

**Advanced Features**:
- **Smart Date Parsing**: "tomorrow", "next Tuesday", "Monday at 3 PM"
- **Time Zone Handling**: Automatic timezone conversion
- **Conflict Detection**: Prevents double-bookings
- **Meeting ID Generation**: Human-readable format (MMDD-HHMM-DURm)

#### Email Service Integration
```python
class EmailService:
    def send_meeting_invitation(self, meeting_details, recipients):
        # 1. Generate professional HTML email
        # 2. Create .ics calendar attachment
        # 3. Send via Gmail SMTP
        # 4. Handle delivery confirmation
        # 5. Log success/failure
```

### 6. Data Flow Architecture

#### Booking Flow
```
User Input → FastAPI → Agent → LLM Processing → Tool Detection 
    ↓
Tool Execution → Calendar API → Email Service → Response Generation
    ↓
HTML Formatting → Redis Storage → User Response
```

#### Session Management
```
Request → Session Lookup (Redis) → Context Loading → Processing 
    ↓
Response Generation → Context Update → Redis Storage → Response
```

## Production Features

### 1. Error Handling
- **Graceful Degradation**: System continues operating during partial failures
- **Retry Logic**: Automatic retry for transient failures
- **Fallback Systems**: LLM, email, and calendar fallbacks
- **User-Friendly Errors**: Clear error messages for users

### 2. Performance Optimization
- **Async Operations**: Non-blocking I/O for all external calls
- **Connection Pooling**: Efficient resource utilization
- **Caching**: Redis-based response and session caching
- **Optimized Models**: Fast LLM selection for production speed

### 3. Security
- **OAuth2 Integration**: Secure Google Calendar access
- **Environment Variables**: No hardcoded secrets
- **Input Validation**: Sanitization of all user inputs
- **Session Security**: Secure session token generation

### 4. Monitoring
- **Health Checks**: Comprehensive system status monitoring
- **Logging**: Structured logging for all components
- **Metrics**: Performance and usage tracking
- **Alerting**: Automatic notification of system issues

## Deployment Architecture

### Container Strategy
```yaml
services:
  chatcal-api:
    image: chatcal-ai:latest
    ports: ["8000:8000"]
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
      - REDIS_URL=redis://redis:6379
    depends_on: [redis]
    
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes: [redis_data:/data]
```

### Scalability Design
- **Stateless Application**: All state stored in Redis
- **Horizontal Scaling**: Multiple API instances supported
- **Load Balancing**: Standard HTTP load balancer compatible
- **Database Scaling**: Redis clustering for high availability

## Technology Stack

### Core Technologies
- **Backend**: Python 3.11+ with FastAPI
- **LLM Framework**: LlamaIndex with Groq integration
- **Database**: Redis for session and memory storage
- **Calendar**: Google Calendar API with OAuth2
- **Email**: Gmail SMTP with HTML templates
- **Deployment**: Docker with docker-compose

### Production Dependencies
```python
# Key packages
fastapi>=0.104.1          # High-performance API framework
llama-index>=0.9.0        # LLM orchestration
llama-index-llms-groq     # Groq integration
redis>=5.0.0              # Session storage
google-auth>=2.0.0        # Google API authentication
aiosmtplib>=3.0.0         # Async email sending
```

## Data Models

### Session Model
```python
class Session:
    session_id: str
    user_info: dict         # Name, email, phone
    conversation_history: list
    created_at: datetime
    last_activity: datetime
```

### Meeting Model  
```python
class Meeting:
    meeting_id: str         # Format: MMDD-HHMM-DURm
    title: str
    date: datetime
    duration_minutes: int
    attendees: list
    google_meet_link: str
    status: str             # confirmed, cancelled
```

This architecture provides a robust, scalable, and production-ready foundation for AI-powered calendar scheduling with comprehensive email integration.