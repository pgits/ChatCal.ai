#!/bin/bash

# Deploy to a completely new Cloud Run service to bypass the stuck old service
set -e

PROJECT_ID="chatcal-ai-prod-monroe919"
OLD_SERVICE="chatcal-ai"
NEW_SERVICE="chatcal-ai-v2"
REGION="us-east1"
IMAGE_TAG="new-service-$(date +%s)"

echo "🚀 Creating completely new Cloud Run service to bypass stuck deployment"
echo "📍 Project: $PROJECT_ID"
echo "🌍 Region: $REGION"
echo "🔄 Old service: $OLD_SERVICE"
echo "🆕 New service: $NEW_SERVICE"

# Build and deploy to new service name
echo ""
echo "🔨 Building fresh image for AMD64/Linux (Cloud Run requirement)..."
docker build --platform linux/amd64 -t gcr.io/$PROJECT_ID/$NEW_SERVICE:$IMAGE_TAG .
docker push gcr.io/$PROJECT_ID/$NEW_SERVICE:$IMAGE_TAG

echo ""
echo "🚀 Deploying to NEW service (bypassing old stuck service)..."
gcloud run deploy $NEW_SERVICE \
  --image gcr.io/$PROJECT_ID/$NEW_SERVICE:$IMAGE_TAG \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLIENT_ID=432729289953-gmo9g4i22onoah53ehiilba6dfgu12qu.apps.googleusercontent.com,MY_EMAIL_ADDRESS=pgits.job@gmail.com,MY_PHONE_NUMBER=6308805488,SMTP_USERNAME=pgits.job@gmail.com,ENVIRONMENT=production,TESTING_MODE=false" \
  --update-secrets="GROQ_API_KEY=groq-api-key:latest,GOOGLE_CLIENT_SECRET=google-client-secret:latest,SMTP_PASSWORD=smtp-password:latest,SECRET_KEY=secret-key:latest" \
  --timeout=300 \
  --max-instances=5

echo ""
echo "🔍 Getting new service URL..."
NEW_SERVICE_URL=$(gcloud run services describe $NEW_SERVICE --platform managed --region $REGION --format 'value(status.url)')

echo ""
echo "✅ NEW SERVICE DEPLOYED!"
echo "🌐 New Service URL: $NEW_SERVICE_URL"
echo "🔍 Test debug endpoint: $NEW_SERVICE_URL/debug-deployment-test"
echo "🔍 Test version: $NEW_SERVICE_URL/version"
echo ""
echo "🔄 After testing, you can update DNS to point to the new service"