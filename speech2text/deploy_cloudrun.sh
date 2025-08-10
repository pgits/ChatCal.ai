#!/bin/bash

# Deploy Kyutai STT to Google CloudRun
# Usage: ./deploy_cloudrun.sh [cpu|gpu] [region]

set -e

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"myunmute"}
SERVICE_NAME="kyutai-stt"
DEPLOYMENT_TYPE=${1:-"cpu"}  # cpu or gpu
REGION=${2:-"us-east1"}

# Set image tag based on deployment type
if [ "$DEPLOYMENT_TYPE" = "gpu" ]; then
    IMAGE_TAG="gcr.io/$PROJECT_ID/$SERVICE_NAME-gpu:latest"
    echo "🚀 Deploying with GPU support..."
else
    IMAGE_TAG="gcr.io/$PROJECT_ID/$SERVICE_NAME-cpu:latest"
    echo "🚀 Deploying CPU-only version..."
fi

echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Image: $IMAGE_TAG"

# Build and push image
echo "📦 Building Docker image..."
docker build \
    --platform linux/amd64 \
    -t $IMAGE_TAG \
    .

echo "📤 Pushing image to Google Container Registry..."
docker push $IMAGE_TAG

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."

if [ "$DEPLOYMENT_TYPE" = "gpu" ]; then
    # Deploy with GPU
    gcloud run deploy $SERVICE_NAME-gpu \
        --image $IMAGE_TAG \
        --platform managed \
        --region $REGION \
        --allow-unauthenticated \
        --port 8080 \
        --memory 8Gi \
        --cpu 4 \
        --gpu 1 \
        --gpu-type nvidia-l4 \
        --timeout 3600 \
        --concurrency 1 \
        --max-instances 3 \
        --min-instances 0 \
        --set-env-vars "DEPLOYMENT_TYPE=gpu" \
        --set-env-vars "CUDA_VISIBLE_DEVICES=0"
else
    # Deploy CPU-only with WebSocket-optimized settings
    gcloud run deploy $SERVICE_NAME-cpu \
        --image $IMAGE_TAG \
        --platform managed \
        --region $REGION \
        --allow-unauthenticated \
        --port 8080 \
        --memory 4Gi \
        --cpu 2 \
        --timeout 3600 \
        --concurrency 10 \
        --max-instances 10 \
        --min-instances 0 \
        --set-env-vars "DEPLOYMENT_TYPE=cpu" \
        --session-affinity
fi

echo "✅ Deployment complete!"

# Get the service URL
if [ "$DEPLOYMENT_TYPE" = "gpu" ]; then
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME-gpu --platform managed --region $REGION --format 'value(status.url)')
else
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME-cpu --platform managed --region $REGION --format 'value(status.url)')
fi

echo ""
echo "🌐 Service URL: $SERVICE_URL"
echo "🩺 Health check: $SERVICE_URL/health"
echo "📡 WebSocket endpoint: ws://${SERVICE_URL#https://}/ws/transcribe"
echo ""
echo "📝 Test with:"
echo "curl $SERVICE_URL/health"