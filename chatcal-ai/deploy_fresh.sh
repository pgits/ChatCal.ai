#!/bin/bash

# Fresh deployment script for ChatCal.ai v0.5.0
# This will delete the existing service and redeploy from current code

set -e

PROJECT_ID="chatcal-ai-prod-monroe919"
SERVICE="chatcal-ai"
REGION="us-east1"
IMAGE_TAG="v0.5.0-fresh-deploy-$(date +%s)"

echo "🚀 Starting fresh deployment of ChatCal.ai v0.5.0"
echo "🏷️  Image tag: $IMAGE_TAG"
echo "📍 Project: $PROJECT_ID"
echo "🌍 Region: $REGION"

# Step 1: Delete existing service
echo ""
echo "🗑️  Step 1: Deleting existing Cloud Run service..."
if gcloud run services delete $SERVICE --region=$REGION --quiet 2>/dev/null; then
    echo "✅ Service deleted successfully"
else
    echo "ℹ️  Service may not exist or already deleted"
fi

# Step 2: Build new image with current code
echo ""
echo "🔨 Step 2: Building Docker image with current v0.5.0 code..."
docker build -t gcr.io/$PROJECT_ID/$SERVICE:$IMAGE_TAG .

# Step 3: Push image
echo ""
echo "📤 Step 3: Pushing image to Container Registry..."
docker push gcr.io/$PROJECT_ID/$SERVICE:$IMAGE_TAG

# Step 4: Deploy fresh service
echo ""
echo "🚀 Step 4: Deploying fresh Cloud Run service..."
gcloud run deploy $SERVICE \
  --image gcr.io/$PROJECT_ID/$SERVICE:$IMAGE_TAG \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLIENT_ID=432729289953-gmo9g4i22onoah53ehiilba6dfgu12qu.apps.googleusercontent.com,MY_EMAIL_ADDRESS=pgits.job@gmail.com,MY_PHONE_NUMBER=6308805488,SMTP_USERNAME=pgits.job@gmail.com,ENVIRONMENT=production,TESTING_MODE=false" \
  --update-secrets="GROQ_API_KEY=groq-api-key:latest,GOOGLE_CLIENT_SECRET=google-client-secret:latest,SMTP_PASSWORD=smtp-password:latest,SECRET_KEY=secret-key:latest" \
  --timeout=300 \
  --max-instances=5

# Step 5: Get service URL
echo ""
echo "📍 Step 5: Getting service URL..."
SERVICE_URL=$(gcloud run services describe $SERVICE --platform managed --region $REGION --format 'value(status.url)')

echo ""
echo "✅ Fresh deployment complete!"
echo "🌐 Service URL: $SERVICE_URL"
echo "🔍 Check version: $SERVICE_URL/version"
echo "🔐 Check auth: $SERVICE_URL/auth/status"
echo ""
echo "🎉 ChatCal.ai v0.5.0 with OAuth persistence is now live!"