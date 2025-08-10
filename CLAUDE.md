## Known Issues
- Adding service account authentication for Google Calendar doesn't work because I don't have the proper account type, Google Workspace.

## Deployment Notes
- Trigger a cold start in the Google RunCloud instead of trying to perform updates.
- Change the timeout from 3 to 5 minutes when uploading a docker build.

## OAuth and Networking
- ✅ **COMPLETED**: Migrated OAuth token storage from Redis to Google Cloud Secret Manager for persistent token storage across Cloud Run container restarts
- **Cost Optimization**: Downgraded Redis from Standard tier (with persistence) back to Basic tier, saving ~$15-20/month
- **Secret Manager Benefits**: 
  - Persistent OAuth refresh tokens (~$0.06-3/month vs $17-33/month for Redis Standard)
  - In-memory access token caching during container lifetime for optimal performance
  - Automatic token refresh on container startup
  - Secure, Google-managed secret storage