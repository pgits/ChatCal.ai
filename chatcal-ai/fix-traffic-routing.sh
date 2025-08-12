#!/bin/bash

# Force all traffic to the latest revision
set -e

PROJECT_ID="chatcal-ai-prod-monroe919"
SERVICE="chatcal-ai"
REGION="us-east1"

echo "🔍 Checking current revisions and traffic allocation..."
gcloud run services describe $SERVICE --region=$REGION --format="table(metadata.name, spec.traffic[].revisionName, spec.traffic[].percent)"

echo ""
echo "🔍 Listing all revisions..."
gcloud run revisions list --service=$SERVICE --region=$REGION --format="table(metadata.name, metadata.creationTimestamp, status.conditions[0].status)"

echo ""
echo "🎯 Getting latest revision..."
LATEST_REVISION=$(gcloud run revisions list --service=$SERVICE --region=$REGION --format="value(metadata.name)" --limit=1)
echo "Latest revision: $LATEST_REVISION"

echo ""
echo "🔄 Setting 100% traffic to latest revision..."
gcloud run services update-traffic $SERVICE --to-revisions=$LATEST_REVISION=100 --region=$REGION

echo ""
echo "✅ Traffic routing updated!"
echo "🔍 Testing in 30 seconds..."
sleep 30

SERVICE_URL=$(gcloud run services describe $SERVICE --platform managed --region $REGION --format 'value(status.url)')
echo ""
echo "🧪 Testing debug endpoint..."
curl -s "$SERVICE_URL/debug-deployment-test" || echo "Still not working - may need new service"

echo "🧪 Testing version..."
curl -s "$SERVICE_URL/version" | jq '.app_version'