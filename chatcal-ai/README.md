# ChatCal.ai - AI-Powered Calendar Assistant

An intelligent AI scheduling assistant powered by Groq's Llama-3.1-8b-instant and LlamaIndex that helps users book appointments on Google Calendar with natural conversation and smart features.

## Features

- 🤖 **Groq-powered LLM**: Fast, efficient conversation using Llama-3.1-8b-instant
- 📅 **Smart Calendar Integration**: Seamless Google Calendar booking with conflict detection
- 🧠 **Conversation Memory**: Persistent context across multi-turn conversations
- 🎨 **HTML-formatted Responses**: Rich, styled responses for better readability
- 🆔 **Custom Meeting IDs**: Human-readable meeting IDs (MMDD-HHMM-DURm format)
- 🗑️ **Smart Cancellation**: Intelligent meeting matching with automatic email notifications
- 🎥 **Google Meet Integration**: Automatic video conference setup for remote meetings
- 📧 **Email Notifications**: Automated booking confirmations and cancellation notices
- 🧪 **Testing Mode**: Configurable testing environment for development
- 🚀 **FastAPI Backend**: High-performance API with Redis session management
- 🔒 **Secure Authentication**: OAuth2 for Google Calendar access
- 🌍 **Timezone-aware**: Smart scheduling across time zones

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Groq API key (get free key at https://console.groq.com/keys)
- Anthropic API key (optional fallback)
- Google Cloud Project with Calendar API enabled
- Google OAuth2 credentials
- SMTP credentials for email notifications

## Quick Start

### 1. Clone the repository
```bash
git clone <repository>
cd chatcal-ai
```

### 2. Set up environment variables
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
- `GROQ_API_KEY`: Your Groq API key (get free key at https://console.groq.com/keys)
- `ANTHROPIC_API_KEY`: Your Anthropic API key (optional fallback)
- `GOOGLE_CLIENT_ID` & `GOOGLE_CLIENT_SECRET`: From Google Cloud Console
- `SECRET_KEY`: Generate a secure secret key
- `MY_PHONE_NUMBER` & `MY_EMAIL_ADDRESS`: Contact information
- `SMTP_USERNAME` & `SMTP_PASSWORD`: Email service credentials
- `TESTING_MODE`: Set to true for development (ignores Peter's email validation)

### 3. Google Calendar Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable Google Calendar API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"
4. Create OAuth2 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Web application"
   - Add authorized redirect URIs:
     - `http://localhost:8000/auth/callback`
     - `https://yourdomain.com/auth/callback` (for production)
   - Save and download the credentials

### 4. Run with Docker

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

The application will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 5. Development Setup (without Docker)

```bash
# Install Poetry
pip install poetry

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Run the application
uvicorn app.api.main:app --reload
```

## Project Structure

```
chatcal-ai/
├── app/
│   ├── core/           # Agent, LLM (Groq), tools, and email service
│   ├── calendar/       # Google Calendar integration
│   ├── api/           # FastAPI endpoints (simple-chat, chat-widget)
│   └── personality/   # System prompts and response templates
├── frontend/          # Web UI with HTML response rendering
├── docker/           # Docker configurations
├── tests/           # Test suite
├── credentials/     # Google credentials (gitignored)
└── docker-compose.yml
```

## API Endpoints

- `POST /chat` - Send a message to the chatbot (with HTML response support)
- `GET /simple-chat` - Simple chat interface for testing
- `GET /chat-widget` - Embeddable chat widget with HTML rendering
- `GET /health` - Health check endpoint
- `POST /sessions` - Create new session
- `GET /auth/login` - Initiate Google OAuth flow
- `GET /auth/callback` - OAuth callback handler

## Deployment

### Deploy to any platform with Docker:

1. Build the production image:
```bash
docker build -t chatcal-ai:latest .
```

2. Push to your container registry:
```bash
docker tag chatcal-ai:latest your-registry/chatcal-ai:latest
docker push your-registry/chatcal-ai:latest
```

3. Deploy using your platform's container service (ECS, GKE, Azure Container Instances, etc.)

### Embed in landing pages:

Add the chat widget to any webpage:
```html
<iframe 
  src="https://your-deployment.com/chat-widget" 
  width="400" 
  height="600"
  frameborder="0">
</iframe>
```

## Key Features

### Conversation Memory
- Persistent conversation context using ChatMemoryBuffer
- Multi-turn dialog support for complex booking flows
- User information extraction and retention

### Smart Meeting Management
- **Custom Meeting IDs**: Format MMDD-HHMM-DURm (e.g., 0731-1400-60m)
- **Intelligent Cancellation**: Matches meetings by user name and date/time
- **Automatic Email Notifications**: Booking confirmations and cancellation notices

### HTML Response Formatting
- Rich, styled responses with proper formatting
- Color-coded status messages (confirmations, cancellations, errors)
- Easy-to-read meeting details and contact information

### Google Meet Integration
- Automatic detection of video meeting requests
- Google Meet link generation and embedding
- Support for both in-person and remote meetings

## LLM Configuration

### Groq Integration (Primary)

The application uses Groq's `Llama-3.1-8b-instant` model for fast, efficient AI responses:

- **Model**: Llama-3.1-8b-instant (high-performance open-source model)
- **API Key**: Required (get free key at https://console.groq.com/keys)
- **Fallback Chain**: Groq → Anthropic → Mock LLM
- **Speed**: Extremely fast inference with low latency

### HuggingFace Integration (Commented Out)

The application has HuggingFace integration code available but commented out due to API access issues:
- **Status**: Disabled until HuggingFace Inference API issues are resolved
- **Model**: Qwen/Qwen2.5-7B-Instruct (available when enabled)
- **Code Location**: See commented sections in `app/core/llm_anthropic.py`

### LLM Fallback Chain

The application implements a robust fallback system:
1. **Primary**: Groq Llama-3.1-8b-instant
2. **Fallback**: Anthropic Claude-3-Sonnet (if Groq fails)
3. **Final Fallback**: Mock LLM (for testing/development)

## Configuration

See `app/config.py` for all available settings. Key configurations:

- `MAX_CONVERSATION_HISTORY`: Number of messages to maintain in context
- `SESSION_TIMEOUT_MINUTES`: Session expiration time
- `DEFAULT_TIMEZONE`: Default timezone for appointments
- `TESTING_MODE`: Enable/disable testing features
- `GROQ_API_KEY`: Groq API key for LLM access
- `ANTHROPIC_API_KEY`: Optional Anthropic API key for fallback

## Testing

```bash
# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app

# Run linting
poetry run black .
poetry run flake8
```

## Security Considerations

- Always use HTTPS in production
- Keep your API keys secure and never commit them
- Implement rate limiting for production deployments
- Use environment-specific configurations
- Regular security audits of dependencies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

[Your chosen license]

## Support

For issues or questions, please open an issue on GitHub or contact pgits.job@gmail.com