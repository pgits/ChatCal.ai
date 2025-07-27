# ChatCal.ai Deployment Guide

## Overview

ChatCal.ai is a Docker-containerized AI-powered calendar assistant that can be deployed to various platforms. This guide covers deployment options and configuration.

## Prerequisites

- Docker and Docker Compose
- Google Calendar API credentials
- Gemini API key
- Redis instance (included in Docker setup)

## Environment Configuration

### Required Environment Variables

Create a `.env` file with the following variables:

```bash
# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# Google Calendar
GOOGLE_CALENDAR_ID=your-email@gmail.com
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Application Settings
APP_NAME=ChatCal.ai
APP_ENV=production
APP_PORT=8000
APP_HOST=0.0.0.0

# Security
SECRET_KEY=generate_a_secure_random_key_here
CORS_ORIGINS=["https://yourdomain.com"]

# Timezone
DEFAULT_TIMEZONE=America/New_York
```

## Local Development

### 1. Clone and Setup

```bash
git clone https://github.com/pgits/ChatCal.ai.git
cd ChatCal.ai
cp .env.example .env
# Edit .env with your credentials
```

### 2. Run with Docker Compose

```bash
docker-compose up --build
```

### 3. Access the Application

- Main API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Production Deployment

### Docker Hub Deployment

1. **Build and Push Image**

```bash
# Build the image
docker build -t chatcal-ai:latest .

# Tag for Docker Hub
docker tag chatcal-ai:latest your-username/chatcal-ai:latest

# Push to Docker Hub
docker push your-username/chatcal-ai:latest
```

2. **Deploy on Server**

```bash
# Pull the image
docker pull your-username/chatcal-ai:latest

# Run with environment file
docker run -d \\
  --name chatcal-ai \\
  --env-file .env \\
  -p 8000:8000 \\
  your-username/chatcal-ai:latest
```

### AWS ECS Deployment

1. **Create Task Definition**

```json
{
  "family": "chatcal-ai",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "chatcal-ai",
      "image": "your-username/chatcal-ai:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "APP_ENV", "value": "production"},
        {"name": "APP_PORT", "value": "8000"}
      ],
      "secrets": [
        {"name": "GEMINI_API_KEY", "valueFrom": "arn:aws:secretsmanager:region:account:secret:gemini-api-key"},
        {"name": "GOOGLE_CLIENT_SECRET", "valueFrom": "arn:aws:secretsmanager:region:account:secret:google-client-secret"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/chatcal-ai",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

2. **Deploy Service**

```bash
aws ecs create-service \\
  --cluster my-cluster \\
  --service-name chatcal-ai \\
  --task-definition chatcal-ai:1 \\
  --desired-count 1 \\
  --launch-type FARGATE \\
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
```

### Kubernetes Deployment

1. **Create ConfigMap**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: chatcal-config
data:
  APP_ENV: "production"
  APP_PORT: "8000"
  REDIS_URL: "redis://redis:6379/0"
```

2. **Create Secret**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: chatcal-secrets
type: Opaque
stringData:
  GEMINI_API_KEY: "your_gemini_api_key"
  GOOGLE_CLIENT_SECRET: "your_google_client_secret"
```

3. **Create Deployment**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chatcal-ai
spec:
  replicas: 2
  selector:
    matchLabels:
      app: chatcal-ai
  template:
    metadata:
      labels:
        app: chatcal-ai
    spec:
      containers:
      - name: chatcal-ai
        image: your-username/chatcal-ai:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: chatcal-config
        - secretRef:
            name: chatcal-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## Monitoring and Logging

### Health Checks

The application provides a health check endpoint at `/health` that monitors:

- Database (Redis) connectivity
- LLM (Gemini) API status
- Calendar service configuration

### Logging Configuration

Set log level via environment variable:

```bash
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### Prometheus Metrics (Optional)

Add prometheus metrics by installing:

```bash
pip install prometheus-fastapi-instrumentator
```

## Security Considerations

### 1. Environment Variables

- Never commit `.env` files to version control
- Use secrets management for production (AWS Secrets Manager, Kubernetes Secrets)
- Rotate API keys regularly

### 2. Network Security

- Use HTTPS in production
- Configure proper CORS origins
- Implement rate limiting
- Use VPC/private networks when possible

### 3. Authentication

- Implement proper OAuth2 flows for Google Calendar
- Consider adding user authentication for multi-tenant deployments
- Use secure session management

## Scaling Considerations

### Horizontal Scaling

- The application is stateless except for Redis sessions
- Can be scaled horizontally by adding more containers
- Consider using a managed Redis service (AWS ElastiCache, Redis Cloud)

### Load Balancing

Configure load balancer for multiple instances:

```nginx
upstream chatcal {
    server chatcal-ai-1:8000;
    server chatcal-ai-2:8000;
    server chatcal-ai-3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://chatcal;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Troubleshooting

### Common Issues

1. **Gemini API Errors**
   - Check API key validity
   - Verify billing is enabled
   - Check rate limits

2. **Google Calendar Issues**
   - Verify OAuth2 credentials
   - Check calendar permissions
   - Ensure calendar ID is correct

3. **Redis Connection Issues**
   - Check Redis URL format
   - Verify Redis is running
   - Check network connectivity

### Debug Mode

Enable debug mode for development:

```bash
APP_ENV=development
LOG_LEVEL=DEBUG
```

### Logs Analysis

Check application logs:

```bash
# Docker
docker logs chatcal-ai

# Kubernetes
kubectl logs deployment/chatcal-ai

# Local
tail -f logs/chatcal.log
```

## Performance Optimization

### 1. Redis Configuration

- Use Redis clustering for high availability
- Configure appropriate memory limits
- Enable Redis persistence if needed

### 2. LLM Optimization

- Implement response caching for common queries
- Use connection pooling
- Consider model selection based on response time requirements

### 3. Calendar API

- Implement caching for calendar data
- Use batch requests when possible
- Optimize query time ranges

## Backup and Recovery

### Database Backup

Redis data backup strategy:

```bash
# Redis backup
redis-cli BGSAVE

# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
redis-cli --rdb /backup/redis_backup_$DATE.rdb
```

### Configuration Backup

- Backup environment configurations
- Version control Docker configurations
- Document deployment procedures

---

For support and questions, please refer to the project repository or contact the development team.