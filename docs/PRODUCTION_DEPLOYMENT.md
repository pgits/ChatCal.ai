# Production Deployment Guide

## Overview

ChatCal.ai v4.0 is production-ready with advanced conversational AI intelligence, comprehensive email integration, and robust error handling. The v4.0 update includes significant user experience improvements:

### V4.0 Production Features:
- **Smart Time Intelligence**: "now" scheduling, past time validation with 15-minute grace period
- **Enhanced Availability**: Shows specific time slots instead of "awaiting confirmation"
- **Direct Google Meet Links**: No artificial security restrictions
- **Timezone Consistency**: UTC-aware processing across all components
- **Improved Error Handling**: User-friendly messages with personality

This guide covers deployment to various platforms.

## Quick Production Checklist

### ✅ Pre-Deployment Requirements

- [ ] Google Calendar API enabled and OAuth2 configured
- [ ] Groq API key obtained (free at https://console.groq.com/keys)
- [ ] Gmail SMTP app password generated
- [ ] Environment variables configured
- [ ] Docker images built and tested
- [ ] Domain name and SSL certificates ready

### ✅ Environment Configuration

Create production `.env` file:

```bash
# LLM Configuration
GROQ_API_KEY=your-groq-api-key
ANTHROPIC_API_KEY=your-anthropic-key-for-fallback

# Google Integration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password

# Security
SECRET_KEY=your-secure-secret-key-min-32-chars

# Contact Information
MY_EMAIL_ADDRESS=pgits.job@gmail.com
MY_PHONE_NUMBER=555-123-4567

# Production Settings
TESTING_MODE=false
ENVIRONMENT=production
```

## Platform-Specific Deployments

### Docker Deployment (Recommended)

#### 1. Build Production Image

```bash
# Clone repository
git clone <your-repo-url>
cd chatcal-ai

# Build image
docker build -t chatcal-ai:latest -f Dockerfile .

# Test locally
docker-compose up -d
```

#### 2. Deploy to Container Registry

```bash
# Tag for your registry
docker tag chatcal-ai:latest your-registry.com/chatcal-ai:v3.0

# Push to registry
docker push your-registry.com/chatcal-ai:v3.0
```

### AWS ECS Deployment

#### 1. Create Task Definition

```json
{
  "family": "chatcal-ai",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "chatcal-ai",
      "image": "your-registry.com/chatcal-ai:v3.0",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "GROQ_API_KEY", "value": "${GROQ_API_KEY}"},
        {"name": "SMTP_USERNAME", "value": "${SMTP_USERNAME}"},
        {"name": "SMTP_PASSWORD", "value": "${SMTP_PASSWORD}"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/chatcal-ai",
          "awslogs-region": "us-east-1"
        }
      }
    }
  ]
}
```

#### 2. Create ECS Service

```bash
# Create cluster
aws ecs create-cluster --cluster-name chatcal-ai-cluster

# Create service
aws ecs create-service \
  --cluster chatcal-ai-cluster \
  --service-name chatcal-ai \
  --task-definition chatcal-ai:1 \
  --desired-count 2 \
  --launch-type FARGATE
```

### Google Cloud Run Deployment

#### 1. Deploy to Cloud Run

```bash
# Enable APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Deploy from source
gcloud run deploy chatcal-ai \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GROQ_API_KEY=$GROQ_API_KEY,SMTP_USERNAME=$SMTP_USERNAME
```

#### 2. Configure Custom Domain

```bash
# Map domain
gcloud run domain-mappings create \
  --service chatcal-ai \
  --domain your-domain.com \
  --region us-central1
```

### Azure Container Instances

#### 1. Create Container Group

```bash
# Create resource group
az group create --name chatcal-ai-rg --location eastus

# Deploy container
az container create \
  --resource-group chatcal-ai-rg \
  --name chatcal-ai \
  --image your-registry.com/chatcal-ai:v3.0 \
  --ports 8000 \
  --dns-name-label chatcal-ai-prod \
  --environment-variables \
    GROQ_API_KEY=$GROQ_API_KEY \
    SMTP_USERNAME=$SMTP_USERNAME \
    SMTP_PASSWORD=$SMTP_PASSWORD
```

## Production Features

### Health Monitoring

The application includes comprehensive health checks:

- **Health Endpoint**: `GET /health`
- **Service Status**: LLM, Calendar, Email validation
- **Resource Monitoring**: Memory, response times
- **Error Tracking**: Automatic logging and alerting

### Security Features

1. **OAuth2 Authentication**: Secure Google Calendar access
2. **Environment Variables**: No hardcoded secrets
3. **HTTPS Enforcement**: SSL/TLS for all communications
4. **Rate Limiting**: Prevent abuse and spam
5. **Input Validation**: Sanitize all user inputs

### Scalability

#### Horizontal Scaling

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  chatcal-api:
    image: chatcal-ai:latest
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
    ports:
      - "8000-8002:8000"
```

#### Load Balancing

```nginx
# nginx.conf
upstream chatcal_backend {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://chatcal_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Monitoring and Observability

### Application Metrics

Monitor these key metrics:

- **Response Time**: API endpoint performance
- **Email Delivery Rate**: SMTP success/failure
- **Booking Success Rate**: End-to-end completion
- **LLM Performance**: Groq response times
- **Error Rates**: 4xx/5xx responses

### Logging

Production logging configuration:

```python
# logging.conf
[loggers]
keys=root,chatcal

[handlers]  
keys=consoleHandler,fileHandler

[formatters]
keys=simpleFormatter

[logger_root]
level=INFO
handlers=consoleHandler,fileHandler

[logger_chatcal]
level=INFO
handlers=consoleHandler,fileHandler
qualname=chatcal
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=INFO
formatter=simpleFormatter
args=('/var/log/chatcal.log',)
```

### Health Checks

```bash
# Container health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

## Backup and Disaster Recovery

### Session Data

- **Redis Persistence**: Enable AOF and RDB snapshots
- **Regular Backups**: Automated Redis data backups
- **Session Recovery**: Graceful handling of Redis failures

### Configuration Management

- **Infrastructure as Code**: Terraform/CloudFormation templates
- **Config Versioning**: Git-based configuration management
- **Secret Management**: HashiCorp Vault or cloud secret services

## Performance Optimization

### Application Tuning

1. **Connection Pooling**: Optimize HTTP connections
2. **Caching**: Redis for session and response caching
3. **Async Processing**: Non-blocking I/O operations
4. **Resource Limits**: CPU and memory constraints

### Database Optimization

```yaml
# Redis optimization
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
  volumes:
    - redis_data:/data
```

## Troubleshooting Guide

### Common Production Issues

1. **Email Delivery Failures**
   ```bash
   # Check SMTP logs
   docker logs chatcal-api | grep -i smtp
   ```

2. **LLM API Timeouts**
   ```bash
   # Monitor Groq API status
   curl -H "Authorization: Bearer $GROQ_API_KEY" https://api.groq.com/openai/v1/models
   ```

3. **Calendar Integration Issues**
   ```bash
   # Verify OAuth token
   docker exec -it chatcal-api python -c "from app.calendar.google_calendar import GoogleCalendarService; print('Calendar OK')"
   ```

### Emergency Procedures

1. **Service Restart**
   ```bash
   docker-compose restart chatcal-api
   ```

2. **Rollback Deployment**
   ```bash
   docker-compose down
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Database Recovery**
   ```bash
   docker-compose exec redis redis-cli BGSAVE
   ```

## Cost Optimization

### API Usage Monitoring

- **Groq API**: Monitor token usage and costs
- **Google Calendar API**: Track quota usage
- **Email Service**: Monitor SMTP usage

### Resource Optimization

- **Right-sizing**: Monitor CPU/memory usage
- **Auto-scaling**: Scale based on traffic patterns
- **Spot Instances**: Use for development/testing

## Conclusion

ChatCal.ai v3.0 is production-ready with:

✅ **Full email integration** with Gmail SMTP
✅ **Conversation memory** for multi-turn dialogs  
✅ **Professional interfaces** (chat widget + simple chat)
✅ **Robust error handling** and fallback systems
✅ **Comprehensive monitoring** and health checks
✅ **Security best practices** implemented
✅ **Scalable architecture** for growth

The system has been tested in production scenarios and successfully processes real bookings with automatic email notifications to all parties.