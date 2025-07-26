# ChatCal.ai - Friendly Google Calendar Booking Assistant

A jovial and encouraging AI chatbot powered by Anthropic's Claude and LlamaIndex that helps users book appointments on Google Calendar with a delightful conversational experience.

## Features

- 🤖 Powered by Anthropic's Claude for natural conversations
- 📅 Seamless Google Calendar integration
- 🌟 Friendly, encouraging personality that makes scheduling fun
- 🐳 Fully containerized with Docker for easy deployment
- 🚀 FastAPI backend with Redis session management
- 🔒 Secure OAuth2 authentication for Google Calendar
- 🌍 Timezone-aware scheduling
- 💬 Context-aware multi-turn conversations

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Anthropic API key (unlimited account)
- Google Cloud Project with Calendar API enabled
- Google OAuth2 credentials

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
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `GOOGLE_CLIENT_ID` & `GOOGLE_CLIENT_SECRET`: From Google Cloud Console
- `SECRET_KEY`: Generate a secure secret key

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
│   ├── core/           # LlamaIndex agent & Anthropic setup
│   ├── calendar/       # Google Calendar integration
│   ├── api/           # FastAPI endpoints
│   └── personality/   # Chatbot personality prompts
├── frontend/          # Web UI (React/Streamlit)
├── docker/           # Docker configurations
├── tests/           # Test suite
├── credentials/     # Google credentials (gitignored)
└── docker-compose.yml
```

## API Endpoints

- `POST /chat` - Send a message to the chatbot
- `GET /health` - Health check endpoint
- `GET /auth/login` - Initiate Google OAuth flow
- `GET /auth/callback` - OAuth callback handler
- `GET /sessions/{session_id}` - Get conversation history

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

## Configuration

See `app/config.py` for all available settings. Key configurations:

- `MAX_CONVERSATION_HISTORY`: Number of messages to maintain in context
- `SESSION_TIMEOUT_MINUTES`: Session expiration time
- `DEFAULT_TIMEZONE`: Default timezone for appointments

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