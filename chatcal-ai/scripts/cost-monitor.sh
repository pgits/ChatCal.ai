#!/bin/bash
# Cost monitoring script for ChatCal.ai on Google Cloud Run

echo "📊 ChatCal.ai Cloud Run Cost Analysis"
echo "====================================="

PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="chatcal-ai"
REGION="us-east1"

echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo ""

# Get current billing month
CURRENT_MONTH=$(date +"%Y-%m")

echo "🔍 Current Usage (This Month):"
echo "------------------------------"

# Get Cloud Run metrics
echo "Cloud Run Requests:"
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
    --filter="timestamp>=\"$CURRENT_MONTH-01\"" \
    --format="value(timestamp)" | wc -l | awk '{print "  Total Requests: " $1}'

echo ""
echo "Cloud Run Instances:"
gcloud run revisions list --service=$SERVICE_NAME --region=$REGION \
    --format="table(metadata.name,status.conditions[0].status,spec.containerConcurrency)"

echo ""
echo "💰 Estimated Costs:"
echo "------------------"
echo "Cloud Run Free Tier Limits:"
echo "  ✅ Requests: 2,000,000/month (FREE)"
echo "  ✅ CPU-seconds: 180,000/month (FREE)"  
echo "  ✅ Memory: 360,000 GiB-seconds/month (FREE)"
echo "  ✅ Network egress: 1 GB/month (FREE)"

echo ""
echo "📈 Service Status:"
echo "-----------------"
gcloud run services describe $SERVICE_NAME --region=$REGION \
    --format="table(status.url,status.conditions[0].status,spec.template.spec.containers[0].resources.limits.memory)"

echo ""
echo "💡 Cost Optimization Tips:"
echo "-------------------------"
echo "1. Min instances set to 0 (scales to zero) ✅"
echo "2. Memory limit: 512Mi (cost efficient) ✅"
echo "3. CPU limit: 1 vCPU (balanced performance) ✅"
echo "4. Concurrency: 100 (maximize instance usage) ✅"
echo "5. Using Secret Manager (6 secrets free) ✅"

echo ""
echo "⚠️  Monitor these potential costs:"
echo "- Requests > 2M/month: $0.40 per 1M requests"
echo "- CPU > 180K seconds/month: $0.00002400 per vCPU-second"  
echo "- Memory > 360K GiB-second/month: $0.00000250 per GiB-second"
echo "- Network egress > 1GB/month: $0.12 per GB"