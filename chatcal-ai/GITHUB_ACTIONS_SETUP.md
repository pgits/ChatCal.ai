# GitHub Actions Setup for ChatCal.ai

This document explains how to set up automated deployment to Google Cloud Run using GitHub Actions.

## Prerequisites

✅ **Completed Setup:**
- Service account `github-actions@chatcal-ai-prod-monroe919.iam.gserviceaccount.com` created
- Required IAM roles granted:
  - `roles/run.admin` - Deploy to Cloud Run
  - `roles/storage.admin` - Push to Google Container Registry
  - `roles/iam.serviceAccountUser` - Act as service account
- GitHub Actions workflow created: `.github/workflows/deploy-cloud-run.yml`

## GitHub Repository Setup

### 1. Add Repository Secret

In your GitHub repository:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `GCP_SA_KEY`
4. Value: Copy the entire JSON content from the service account key file created earlier

### 2. Push Code to GitHub

The workflow will trigger on:
- Push to `main` branch
- Push to `deploy-pipeline` branch
- Manual workflow dispatch

### 3. Monitor Deployment

1. Go to **Actions** tab in your GitHub repository
2. Click on the running workflow
3. Monitor the deployment progress
4. Check the final step for the deployed service URL

## Workflow Features

✅ **Automated Build & Deploy:**
- Builds Docker image using GitHub's infrastructure
- Pushes to Google Container Registry (gcr.io)
- Deploys to Cloud Run with correct environment variables
- Sets the correct client ID: `432729289953-1di05ajntobgvv0aakgjahnrtp60491j.apps.googleusercontent.com`

✅ **Environment Variables Set:**
- `GOOGLE_CLIENT_ID=432729289953-1di05ajntobgvv0aakgjahnrtp60491j.apps.googleusercontent.com`
- `MY_EMAIL_ADDRESS=pgits.job@gmail.com`
- `MY_PHONE_NUMBER=555-123-4567`
- `SMTP_USERNAME=pgits.job@gmail.com`
- `ENVIRONMENT=production`
- `TESTING_MODE=false`

✅ **Secrets from Secret Manager:**
- `GROQ_API_KEY` from `groq-api-key`
- `GOOGLE_CLIENT_SECRET` from `google-client-secret`
- `SMTP_PASSWORD` from `smtp-password`
- `SECRET_KEY` from `secret-key`

## Testing the Pipeline

### 1. Push Changes
```bash
git add .
git commit -m "test: Trigger GitHub Actions deployment"
git push origin deploy-pipeline
```

### 2. Manual Trigger
1. Go to **Actions** tab
2. Select "Deploy to Cloud Run" workflow
3. Click **Run workflow**
4. Choose branch and click **Run workflow**

## Benefits

🚀 **Faster Deployments**: Bypasses slow Cloud Build issues
⚡ **Reliable**: Uses GitHub's infrastructure for building
🔒 **Secure**: Service account with minimal required permissions
🎯 **Accurate**: Ensures correct client ID deployment
📊 **Visible**: Full deployment logs in GitHub Actions

## Troubleshooting

### Common Issues:

1. **Permission Denied**: Check that the service account has all required roles
2. **Secret Not Found**: Verify `GCP_SA_KEY` secret is properly formatted JSON
3. **Build Failures**: Check Dockerfile and source code for issues
4. **Deployment Timeout**: Cloud Run service may need more time to start

### Debug Steps:

1. Check GitHub Actions logs for detailed error messages
2. Verify GCP project ID and service names in workflow
3. Test service account permissions with gcloud CLI
4. Ensure all required secrets exist in Secret Manager