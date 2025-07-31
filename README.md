# ChatCal.ai

An AI-powered Google Calendar booking assistant with multiple LLM integrations and local model support.

## Overview

ChatCal.ai is a comprehensive calendar booking solution that combines the power of large language models with Google Calendar integration. The project includes both cloud-based LLM options (Anthropic Claude, Google Gemini) and local model support through Hugging Face transformers.

## Project Structure

```
chatcal.ai/
├── chatcal-ai/           # Main application
│   ├── app/              # FastAPI backend
│   ├── frontend/         # Web UI
│   ├── docker/           # Containerization
│   └── docs/             # Documentation
├── hf-lama.py           # Local LLM with Hugging Face & LlamaIndex
├── llama-anthropic.py   # Anthropic Claude integration
├── models/              # Downloaded Hugging Face models
└── docs/                # Project documentation
```

## Components

### 1. ChatCal.ai Core Application
- **Location**: `./chatcal-ai/`
- **Description**: Full-featured calendar booking assistant with web interface
- **Features**: 
  - Google Calendar integration
  - FastAPI backend with Redis sessions
  - Docker containerization
  - OAuth2 authentication
  - Multiple LLM provider support

### 2. Local LLM Integration (hf-lama.py)
- **Purpose**: Run language models locally using Hugging Face transformers
- **Features**:
  - Support for Qwen2.5, Phi-3, and other open models
  - LlamaIndex integration for RAG capabilities
  - Document loading and vector indexing
  - Interactive chat interface
  - SSL certificate handling for NLTK downloads

### 3. Cloud LLM Scripts
- **llama-anthropic.py**: Integration with Anthropic's Claude API
- **simpletest.py**: Testing utilities

## Quick Start

### Option 1: Full Application (Recommended)
```bash
cd chatcal-ai
docker-compose up -d
```
Access at: http://localhost:8000

### Option 2: Local LLM Only
```bash
python3 hf-lama.py
```

## Requirements

### For Full Application:
- Docker & Docker Compose
- Google Cloud Project with Calendar API
- Anthropic API key (optional)
- Google Gemini API key (optional)

### For Local LLM:
- Python 3.11+
- PyTorch
- Transformers
- LlamaIndex
- ~8GB+ RAM (for 7B models)

## Configuration

1. **Google Calendar Setup**: Follow the guide in `chatcal-ai/docs/google-oauth-setup.md`
2. **API Keys**: Set environment variables for your chosen LLM providers
3. **Model Selection**: Edit `hf-lama.py` to choose your preferred local model

## Available Models (Local)

- **Qwen2.5-7B-Instruct**: High-quality general purpose model
- **Qwen2.5-3B-Instruct**: Lighter version for resource-constrained environments  
- **Qwen2.5-1.5B-Instruct**: Ultra-lightweight option
- **Phi-3-mini-128k**: Microsoft's efficient model with large context

## Features

### Cloud Integration
- ✅ Anthropic Claude (Sonnet, Haiku)
- ✅ Google Gemini Pro
- ✅ Google Calendar API
- ✅ OAuth2 authentication
- ✅ Session management

### Local Capabilities
- ✅ Local model inference
- ✅ Document RAG with LlamaIndex
- ✅ Vector embeddings
- ✅ Interactive chat
- ✅ SSL/NLTK handling

### Deployment
- ✅ Docker containerization
- ✅ Docker Compose orchestration
- ✅ Development & production configs
- ✅ Health checks & monitoring

## Documentation

- [Main Application README](./chatcal-ai/README.md) - Detailed setup instructions
- [Google OAuth Setup](./chatcal-ai/docs/google-oauth-setup.md) - Calendar integration guide
- [LinkedIn Integration](./chatcal-ai/docs/linkedin-google-calendar-integration.md) - Business use cases
- [Deployment Guide](./chatcal-ai/DEPLOYMENT.md) - Production deployment

## Development

### Testing Local Models
```bash
# Test different model sizes
python3 hf-lama.py  # Uses Qwen2.5-7B by default

# Edit the script to try other models:
# config = model_configs["qwen2.5-3b"]  # Lighter option
# config = model_configs["phi3-mini"]   # Microsoft model
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Test your changes with both local and cloud models
4. Submit a pull request

## Support

- **Issues**: Open GitHub issues for bugs or feature requests
- **Documentation**: Check the `docs/` directories for detailed guides
- **Contact**: pgits.job@gmail.com

## License

See individual component licenses in their respective directories.