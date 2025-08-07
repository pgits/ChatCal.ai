# Kyutai STT CloudRun Deployment

Deploy Kyutai Speech-to-Text models to Google CloudRun with optional GPU support.

## 🚀 Quick Deployment

### 1. CPU-Only Deployment (Recommended for testing)

```bash
# Set your project ID
export GOOGLE_CLOUD_PROJECT="myunmute"

# Deploy CPU version
./deploy_cloudrun.sh cpu us-east1
```

### 2. GPU-Enabled Deployment (For production performance)

```bash
# Deploy GPU version  
./deploy_cloudrun.sh gpu us-east1
```

## 📋 Prerequisites

1. **Google Cloud SDK** installed and authenticated
2. **Docker** installed and running
3. **Google Cloud Project** with billing enabled
4. **Container Registry API** enabled
5. **Cloud Run API** enabled

```bash
# Enable required APIs
gcloud services enable containerregistry.googleapis.com
gcloud services enable run.googleapis.com

# Authenticate Docker with GCR
gcloud auth configure-docker
```

## 🏗️ Architecture

### CPU Version Features:
- ✅ No GPU requirements = Lower cost
- ✅ Auto-scaling from 0 to 10 instances
- ✅ ~300-1000ms latency (acceptable for many use cases)
- ✅ 4GB RAM, 2 CPU cores per instance
- ✅ Concurrent requests: 10 per instance

### GPU Version Features:
- 🚀 NVIDIA L4 GPU acceleration 
- 🚀 ~50-200ms latency (production quality)
- 🚀 Higher accuracy and throughput
- 💰 Higher cost - scales 0 to 3 instances
- 💰 8GB RAM, 4 CPU + 1 GPU per instance
- 🔒 1 concurrent request per instance (GPU limitation)

## 🛠️ API Endpoints

### REST API
```bash
# Health check
curl https://your-service-url/health

# Transcribe audio (base64 encoded)
curl -X POST https://your-service-url/transcribe \
  -H "Content-Type: application/json" \
  -d '{"audio": "base64-encoded-audio-data"}'
```

### WebSocket API
```bash
# Real-time transcription
wscat -c wss://your-service-url/ws/transcribe
```

## 🧪 Testing

### Test the deployed service:

```bash
# Test all endpoints
python test_client.py --url https://your-service-url --test all

# Test specific functionality
python test_client.py --url https://your-service-url --test health
python test_client.py --url https://your-service-url --test websocket --duration 10
python test_client.py --url https://your-service-url --test microphone --duration 15
```

## 💰 Cost Optimization

### CPU Version Costs:
- **Idle**: $0 (scales to zero)
- **Active**: ~$0.05/hour per instance
- **Memory**: 4GB at $0.0000025/GB-second
- **CPU**: 2 vCPU at $0.0000625/vCPU-second

### GPU Version Costs:
- **Idle**: $0 (scales to zero) 
- **Active**: ~$0.50/hour per instance (includes GPU)
- **GPU**: NVIDIA L4 at ~$0.35/hour
- **Memory**: 8GB + faster CPU cores

### Cost Control Strategy:
1. **Start with CPU version** for development/testing
2. **Switch to GPU** only when you need < 200ms latency
3. **Set max instances** to control costs
4. **Use min instances = 0** to scale to zero when idle
5. **Monitor usage** via Google Cloud Console

## 🔧 Configuration Options

### Environment Variables:
- `HF_HOME=/tmp/huggingface` - Cache location
- `TRANSFORMERS_CACHE=/tmp/huggingface` - Model cache
- `PORT=8080` - Server port
- `HOST=0.0.0.0` - Server host

### Model Selection:
Edit the `hf_repo` parameter in server files:
- `kyutai/stt-1b-en_fr` - English/French, 1B params (default)
- `kyutai/stt-2.6b-en` - English only, 2.6B params, better accuracy

## 📊 Performance Benchmarks

### CPU Version (4GB RAM, 2 vCPU):
- **Model Loading**: 10-30 seconds (cold start)
- **Processing Latency**: 300-1000ms per chunk  
- **Throughput**: 2-5 chunks/second
- **Memory Usage**: 2-3GB
- **Concurrent Users**: Up to 50 (with 10 instances)

### GPU Version (8GB RAM, 4 vCPU, NVIDIA L4):
- **Model Loading**: 5-15 seconds (cold start)
- **Processing Latency**: 50-200ms per chunk
- **Throughput**: 10-20 chunks/second
- **Memory Usage**: 4-6GB RAM + 8GB GPU
- **Concurrent Users**: Up to 3 (GPU instances)

## 🚨 Troubleshooting

### Common Issues:

1. **Cold Start Timeout**:
   - Increase timeout to 600s for first deployment
   - Models download on first request (~2-5GB)

2. **Out of Memory**:
   - CPU version: Increase memory to 8GB
   - GPU version: Check GPU memory usage

3. **Authentication Errors**:
   ```bash
   gcloud auth login
   gcloud auth configure-docker
   ```

4. **Build Failures**:
   ```bash
   # Use AMD64 platform for CloudRun
   docker build --platform linux/amd64 ...
   ```

5. **GPU Not Available**:
   - Check region supports GPU instances
   - Verify quota limits for GPUs

### Logs and Monitoring:
```bash
# View service logs
gcloud logging read "resource.type=cloud_run_revision"

# Monitor metrics
gcloud run services describe kyutai-stt-cpu --region us-east1
```

## 🔄 Updating the Service

### Update deployment:
```bash
# Build and deploy new version
./deploy_cloudrun.sh cpu us-east1

# Traffic management (gradual rollout)
gcloud run services update-traffic kyutai-stt-cpu \
  --to-revisions=LATEST=50,PREVIOUS=50
```

### Rolling back:
```bash
# Rollback to previous version
gcloud run services update-traffic kyutai-stt-cpu \
  --to-revisions=PREVIOUS=100
```

## 📝 Next Steps

1. **Start with CPU deployment** to test integration
2. **Monitor performance** and costs
3. **Switch to GPU** if you need < 200ms latency
4. **Integrate with your application** via REST/WebSocket APIs
5. **Set up monitoring** and alerting
6. **Consider hybrid approach**: CPU for dev, GPU for prod

## 🔗 Related Files

- `cloudrun_server.py` - CPU-only FastAPI server
- `cloudrun_server_gpu.py` - GPU-accelerated server  
- `Dockerfile` - Multi-stage build for both versions
- `deploy_cloudrun.sh` - Deployment automation script
- `test_client.py` - Testing and validation client
- `requirements.txt` - Python dependencies