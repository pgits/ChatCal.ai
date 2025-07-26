# 🚀 How to Integrate Google Calendar API with Your AI Chatbot

Building an AI appointment scheduler? Here's a step-by-step guide to set up Google Calendar API OAuth2 authentication for your chatbot project.

## 📋 Prerequisites
- Google account with calendar access
- Google Cloud Console access
- Your web application (localhost for development)

## 🔧 Step-by-Step Setup

### 1️⃣ Access Google Cloud Console
Navigate to https://console.cloud.google.com and sign in with your Google account.

### 2️⃣ Create a New Project
- Click the project dropdown → "New Project"
- Name it (e.g., "ChatCal-AI")
- Click "Create" and wait for completion

### 3️⃣ Enable Google Calendar API
- Go to **APIs & Services** → **Library**
- Search for "Google Calendar API"
- Click on it and press **ENABLE**

### 4️⃣ Configure OAuth Consent Screen
- Navigate to **APIs & Services** → **OAuth consent screen**
- Select "External" user type
- Fill in:
  - App name: Your chatbot name
  - Support email: Your email
  - Developer contact: Your email
- Add scopes:
  - `https://www.googleapis.com/auth/calendar`
  - `https://www.googleapis.com/auth/calendar.events`
- Add test users if in testing mode

### 5️⃣ Create OAuth2 Credentials
- Go to **APIs & Services** → **Credentials**
- Click **+ CREATE CREDENTIALS** → **OAuth client ID**
- Select "Web application"
- Add authorized redirect URIs:
  - `http://localhost:8000/auth/callback` (for development)
  - Your production URLs later
- Click **CREATE**

### 6️⃣ Save Your Credentials
⚠️ **IMPORTANT**: Copy these immediately!
- **Client ID**: Your OAuth2 client identifier
- **Client Secret**: Your OAuth2 secret key

### 7️⃣ Configure Your Application
Add to your environment variables:
```
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

## 🛡️ Security Best Practices
✅ Never commit credentials to version control
✅ Use environment variables
✅ Store secrets securely in production
✅ Implement proper token refresh logic
✅ Use HTTPS in production

## 🎯 Common Use Cases
- AI appointment schedulers
- Calendar management bots
- Meeting automation tools
- Availability checkers
- Event creation assistants

## 💡 Pro Tips
1. Start with "Testing" mode for development
2. Add all redirect URIs you'll need upfront
3. Download the JSON credentials as backup
4. Monitor API usage in Google Console
5. Implement exponential backoff for rate limits

## 🚨 Troubleshooting
- **"Access blocked"**: Add user to test users
- **"Invalid redirect"**: URIs must match exactly
- **"Scope error"**: Ensure calendar scopes are added

## 🔗 Resources
- Google Calendar API Docs: https://developers.google.com/calendar
- OAuth2 Guide: https://developers.google.com/identity/protocols/oauth2
- API Console: https://console.cloud.google.com

---

💬 Building something cool with Google Calendar API? Share your project below!

#GoogleCalendarAPI #OAuth2 #APIIntegration #WebDevelopment #Chatbots #AI #TechTutorial #Programming #GoogleCloud #DeveloperTips