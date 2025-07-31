# 🚀 ChatCal.ai - AI-Powered Scheduling Assistant

## LinkedIn Post Diagram: Complete Feature Overview & Setup Guide

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           🤖 ChatCal.ai Features                            │
│                     Peter Michael Gits' AI Scheduling Assistant             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              🎯 CORE FEATURES                               │
├─────────────────────────────────────────────────────────────────────────────┤
│ ✅ Natural Language Processing    │ ✅ Smart Contact Collection             │
│    • "Book 15 mins with Peter"    │    • Name + Email OR Phone required    │
│    • "Tomorrow at 2pm works"       │    • Flexible requirements             │
│                                   │    • Peter's contact always available   │
│                                   │                                        │
│ ✅ Intelligent Time Management    │ ✅ Multi-Format Meeting Support        │
│    • Real-time availability       │    • Business consultations (60 min)  │
│    • Conflict detection           │    • Quick discussions (30 min)       │
│    • Auto-scheduling              │    • Project meetings (60 min)        │
│                                   │    • Advisory sessions (90 min)       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            🎥 GOOGLE MEET INTEGRATION                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ ✅ Automatic Video Conference Creation                                      │
│    • Detects: "Google Meet", "video call", "online meeting"               │
│    • Real Google Meet links generated automatically                        │
│    • Works with all meeting types                                          │
│                                                                             │
│ 📝 Example Request:                                                         │
│    "Hi, I need a Google Meet call with Peter tomorrow at 3pm"             │
│                                                                             │
│ 🔗 Result:                                                                  │
│    ✅ Meeting scheduled ✅ Google Meet link: meet.google.com/abc-def-ghi    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              📧 EMAIL SYSTEM                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ ✅ Dual Email Invitations        │ ✅ Rich Calendar Attachments           │
│    • Sent to both Peter & user   │    • .ics calendar files              │
│    • Professional HTML templates │    • Google Meet links included       │
│    • Automatic after booking     │    • Complete meeting details         │
│                                   │                                        │
│ ✅ Smart Email Collection         │ ✅ Branded Communication              │
│    • "Want email invitation?"    │    • ChatCal.ai branding              │
│    • Optional but encouraged     │    • Professional formatting          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            🧠 AI CAPABILITIES                               │
├─────────────────────────────────────────────────────────────────────────────┤
│ ✅ Claude Sonnet 4 Integration   │ ✅ Context-Aware Conversations        │
│    • Latest Anthropic AI model   │    • Remembers user details           │
│    • Advanced reasoning          │    • Maintains conversation flow      │
│    • Professional responses      │    • Handles complex requests         │
│                                   │                                        │
│ ✅ Information Extraction         │ ✅ Intelligent Error Handling         │
│    • Names from "This is Betty"  │    • Graceful conflict resolution     │
│    • Phone: "call me at 555..."  │    • Alternative time suggestions     │
│    • Complex multi-part requests │    • User-friendly error messages     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           🔧 TECHNICAL ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ Backend                          │ Frontend                               │
│ • FastAPI REST API              │ • Simple HTML/JS chat interface       │
│ • Redis session management      │ • Real-time messaging                 │
│ • Google Calendar API           │ • Mobile-responsive design            │
│ • SMTP email service            │ • Clean, professional UI              │
│                                  │                                        │
│ AI & Integration                 │ Deployment                             │
│ • LlamaIndex ReActAgent         │ • Docker containerization             │
│ • Anthropic Claude Sonnet 4     │ • Environment-based config            │
│ • Google OAuth2 authentication  │ • Production-ready setup              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              📋 SETUP GUIDE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1️⃣ Prerequisites                                                           │
│    • Python 3.9+                                                          │
│    • Google Cloud Project                                                  │
│    • Anthropic API key                                                     │
│                                                                             │
│ 2️⃣ Google Calendar Setup                                                   │
│    • Enable Google Calendar API                                            │
│    • Create OAuth2 credentials                                             │
│    • Run: python3 complete_oauth.py                                        │
│                                                                             │
│ 3️⃣ Environment Configuration                                               │
│    • Copy .env.example to .env                                             │
│    • Add your API keys:                                                    │
│      - ANTHROPIC_API_KEY=your_key_here                                     │
│      - GOOGLE_CALENDAR_ID=your_email@gmail.com                            │
│      - MY_PHONE_NUMBER=+1234567890                                         │
│      - MY_EMAIL_ADDRESS=your_email@gmail.com                              │
│                                                                             │
│ 4️⃣ Dependencies & Launch                                                   │
│    • pip install -r requirements.txt                                       │
│    • python3 -m uvicorn app.api.main:app --reload                         │
│    • Visit: http://localhost:8000/simple-chat                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            💡 USAGE EXAMPLES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ 🗣️ User: "Book 15 minutes with Peter, this is Betty, have him call me     │
│           at 630 880 5488 Friday, please show me available morning times" │
│                                                                             │
│ 🤖 ChatCal: ✅ Name: Betty ✅ Phone: 630-880-5488                         │
│            "Here are Friday morning slots: 9:00 AM, 10:30 AM, 11:00 AM"  │
│                                                                             │
│ 🗣️ User: "I need a Google Meet with Peter Wednesday at 2pm for an hour"   │
│                                                                             │
│ 🤖 ChatCal: ✅ Meeting booked ✅ Google Meet: meet.google.com/xyz-abc-123  │
│            📧 Email invitations sent to both parties                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           🚀 DEVELOPMENT JOURNEY                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ Phase 1: Core Scheduling (anthropic-sonnet branch)                         │
│ • Replaced Gemini with Claude Sonnet 4                                     │
│ • Built intelligent contact collection                                     │
│ • Added email invitation system                                            │
│                                                                             │
│ Phase 2: Google Meet Integration (google-meet branch)                      │
│ • Added video conference detection                                          │
│ • Integrated Google Calendar conferenceData API                            │
│ • Enhanced email templates with Meet links                                 │
│                                                                             │
│ Key Learnings:                                                              │
│ • Natural language processing for scheduling                               │
│ • Google Calendar API advanced features                                    │
│ • Professional AI assistant development                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                             🎯 KEY BENEFITS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ For Users:                          │ For Business:                        │
│ • Natural conversation scheduling   │ • 24/7 availability                  │
│ • No complex forms or interfaces   │ • Professional brand presence        │
│ • Automatic calendar integration   │ • Reduced scheduling overhead        │
│ • Google Meet links on demand      │ • Enhanced client experience        │
│                                     │                                      │
│ For Developers:                     │ For AI Enthusiasts:                 │
│ • Modern Python/FastAPI stack      │ • Claude Sonnet 4 integration       │
│ • Clean, extensible architecture   │ • Real-world AI application         │
│ • Production-ready deployment      │ • Advanced prompt engineering       │
└─────────────────────────────────────────────────────────────────────────────┘

Built with ❤️ using Claude Sonnet 4, Google Calendar API, and modern Python
```

## LinkedIn Post Caption Ideas:

**Option 1 - Technical Focus:**
"🚀 Just completed ChatCal.ai - an AI-powered scheduling assistant that transforms how we book meetings! Built with Claude Sonnet 4, it handles natural language requests, creates Google Meet links automatically, and sends professional email invitations. The AI extracts contact info from conversations like 'This is Betty, call me at 630-880-5488' and books meetings intelligently. #AI #Python #GoogleMeet #Automation"

**Option 2 - Business Value:**
"💡 Solving the scheduling headache with AI! ChatCal.ai lets clients book time using natural conversation - no forms, no back-and-forth emails. Just say 'Book a Google Meet with Peter tomorrow at 2pm' and it handles everything: calendar conflicts, Google Meet links, email invitations. The future of client onboarding! #ClientExperience #AI #BusinessAutomation"

**Option 3 - Developer Journey:**
"🔧 From idea to production: Building ChatCal.ai taught me advanced Google Calendar API integration, AI prompt engineering with Claude Sonnet 4, and creating seamless user experiences. The system now handles complex requests like 'Book 15 minutes Friday morning' and creates real Google Meet conferences automatically. Open to discussing the technical architecture! #SoftwareDevelopment #AI #GoogleAPI"