"""Main FastAPI application for ChatCal.ai."""

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from datetime import datetime
import uuid
import json
import logging
from typing import Dict, Any, Optional

from app.config import settings
from app.api.models import (
    ChatRequest, ChatResponse, StreamChatResponse, SessionCreate, SessionResponse,
    ConversationHistory, HealthResponse, ErrorResponse, AuthRequest, AuthResponse
)
from app.api.chat_widget import router as chat_widget_router
from app.api.simple_chat import router as simple_chat_router
from app.core.session import session_manager
from app.calendar.auth import CalendarAuth
from app.core.exceptions import (
    ChatCalException, AuthenticationError, CalendarError, 
    LLMError, ValidationError, RateLimitError
)
from app.core.llm_gemini import gemini_llm

# Create FastAPI app
app = FastAPI(
    title="ChatCal.ai",
    description="AI-powered calendar assistant for booking appointments",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log testing mode status on startup
if settings.testing_mode:
    logger.info("🧪 TESTING MODE ENABLED - Peter's email will be treated as regular user email")
else:
    logger.info("📧 Production mode - Peter's email will receive special formatting")

# Calendar auth instance
calendar_auth = CalendarAuth()

# Include routers
app.include_router(chat_widget_router)
app.include_router(simple_chat_router)


# Global exception handlers
@app.exception_handler(ChatCalException)
async def chatcal_exception_handler(request: Request, exc: ChatCalException):
    """Handle custom ChatCal exceptions."""
    logger.error(f"ChatCal exception: {exc.message}", extra={"details": exc.details})
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Invalid request data",
            "details": {"validation_errors": exc.errors()},
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    """Handle internal server errors."""
    logger.error(f"Internal server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred. Please try again later.",
            "details": {},
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with basic information."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ChatCal.ai</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            .container { background: white; padding: 40px; border-radius: 10px; max-width: 800px; margin: 0 auto; }
            h1 { color: #2c3e50; text-align: center; }
            .feature { background: #e8f5e9; padding: 15px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #4caf50; }
            .api-link { background: #e3f2fd; padding: 15px; margin: 15px 0; border-radius: 8px; text-align: center; }
            a { color: #1976d2; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📅 Schedule Time with Peter Michael Gits</h1>
            <p style="text-align: center; font-size: 18px; color: #666;">
                Book consultations, meetings, and advisory sessions with Peter
            </p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="/chat-widget" style="background: #4caf50; color: white; padding: 15px 40px; font-size: 20px; border-radius: 8px; text-decoration: none; display: inline-block;">
                    Book an Appointment Now
                </a>
            </div>
            
            <div class="feature">
                <h3>💼 Professional Consultations</h3>
                <p>Schedule one-on-one business consultations and advisory sessions with Peter Michael Gits</p>
            </div>
            
            <div class="feature">
                <h3>🤖 AI-Powered Scheduling</h3>
                <p>Our intelligent assistant helps you find the perfect time that works for both you and Peter</p>
            </div>
            
            <div class="feature">
                <h3>📧 Instant Confirmation</h3>
                <p>Receive immediate confirmation and calendar invitations for your scheduled meetings</p>
            </div>
            
            <div class="api-link">
                <h3>🛠️ API Documentation</h3>
                <p>
                    <a href="/docs">Interactive API Docs (Swagger)</a> | 
                    <a href="/redoc">Alternative Docs (ReDoc)</a>
                </p>
            </div>
            
            <div style="text-align: center; margin-top: 30px; color: #888;">
                <p>Version 0.1.0 | Built with FastAPI & LlamaIndex</p>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    services = {}
    
    # Check session storage (Redis or in-memory fallback)
    try:
        # Test session creation to verify session storage is working
        test_session = session_manager.create_session({"test": True})
        if test_session and session_manager.get_session(test_session):
            session_manager.delete_session(test_session)
            if session_manager.redis_available:
                services["database"] = "healthy"
            else:
                services["database"] = "healthy_fallback"  # Working with in-memory
        else:
            services["database"] = "unhealthy"
    except Exception as e:
        logger.error(f"Session storage health check failed: {e}")
        services["database"] = "unhealthy"
    
    # Check Groq LLM (via anthropic_llm interface)
    try:
        from app.core.llm_anthropic import anthropic_llm
        if anthropic_llm.test_connection():
            services["llm"] = "healthy"
        else:
            services["llm"] = "unhealthy"
    except Exception as e:
        logger.error(f"LLM health check failed: {e}")
        services["llm"] = "not_configured"
    
    # Add testing mode status
    services["testing_mode"] = "enabled" if settings.testing_mode else "disabled"
    
    # Check Calendar service
    try:
        if calendar_auth.client_id and calendar_auth.client_secret:
            services["calendar"] = "ready"
        else:
            services["calendar"] = "not_configured"
    except Exception as e:
        logger.error(f"Calendar health check failed: {e}")
        services["calendar"] = "unhealthy"
    
    overall_status = "healthy" if all(status in ["healthy", "ready"] for status in services.values()) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        version="0.1.0",
        timestamp=datetime.utcnow(),
        services=services
    )


@app.post("/sessions", response_model=SessionResponse)
async def create_session(request: SessionCreate):
    """Create a new chat session."""
    try:
        session_id = session_manager.create_session(request.user_data)
        
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create session"
            )
        session_data = session_manager.get_session(session_id)
        
        if not session_data:
            raise HTTPException(status_code=500, detail="Failed to create session")
        
        return SessionResponse(
            session_id=session_id,
            created_at=datetime.fromisoformat(session_data["created_at"]),
            last_activity=datetime.fromisoformat(session_data["last_activity"]),
            is_active=True
        )
    except Exception as e:
        logger.error(f"Session creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session. Please try again."
        )


@app.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get session information."""
    session_data = session_manager.get_session(session_id)
    
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        session_id=session_id,
        created_at=datetime.fromisoformat(session_data["created_at"]),
        last_activity=datetime.fromisoformat(session_data["last_activity"]),
        is_active=True
    )


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    success = session_manager.delete_session(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session deleted successfully"}


@app.get("/sessions/{session_id}/history", response_model=ConversationHistory)
async def get_conversation_history(session_id: str):
    """Get conversation history for a session."""
    session_data = session_manager.get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    history = session_manager.get_conversation_history(session_id)
    
    return ConversationHistory(
        session_id=session_id,
        messages=history.get("messages", []) if history else [],
        created_at=datetime.fromisoformat(session_data["created_at"])
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with the AI assistant."""
    print(f"🚨 PRODUCTION DEBUG: Chat endpoint called with message: '{request.message}' session: {request.session_id}")
    try:
        # Create session if not provided
        if not request.session_id:
            request.session_id = session_manager.create_session()
        
        # Get or create conversation
        conversation = session_manager.get_or_create_conversation(request.session_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get response from agent
        print(f"🚨 PRODUCTION DEBUG: About to call conversation.get_response()")
        response = conversation.get_response(request.message)
        print(f"🚨 PRODUCTION DEBUG: Agent response received: '{response[:100]}...'")
        
        # Store conversation history
        session_manager.store_conversation_history(request.session_id)
        
        return ChatResponse(
            response=response,
            session_id=request.session_id,
            timestamp=datetime.utcnow(),
            tools_used=None  # Will implement tool tracking later
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@app.post("/chat/stream")
async def stream_chat(request: ChatRequest):
    """Stream chat response from the AI assistant."""
    try:
        # Create session if not provided
        if not request.session_id:
            request.session_id = session_manager.create_session()
        
        # Get or create conversation
        conversation = session_manager.get_or_create_conversation(request.session_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Session not found")
        
        async def generate_stream():
            """Generate streaming response."""
            try:
                for token in conversation.get_streaming_response(request.message):
                    chunk = StreamChatResponse(
                        token=token,
                        session_id=request.session_id,
                        is_complete=False
                    )
                    yield f"data: {chunk.model_dump_json()}\n\n"
                
                # Send completion signal
                final_chunk = StreamChatResponse(
                    token="",
                    session_id=request.session_id,
                    is_complete=True
                )
                yield f"data: {final_chunk.model_dump_json()}\n\n"
                
                # Store conversation history
                session_manager.store_conversation_history(request.session_id)
                
            except Exception as e:
                error_chunk = {
                    "error": str(e),
                    "session_id": request.session_id,
                    "is_complete": True
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stream chat error: {str(e)}")


@app.get("/auth/login", response_model=AuthResponse)
async def google_auth_login(request: Request, state: Optional[str] = None):
    """Initiate Google OAuth login."""
    try:
        auth_url, oauth_state = calendar_auth.get_authorization_url(state)
        
        return AuthResponse(
            auth_url=auth_url,
            state=oauth_state
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auth error: {str(e)}")


@app.get("/auth/callback")
async def google_auth_callback(request: Request, code: str, state: str):
    """Handle Google OAuth callback."""
    try:
        # Reconstruct the authorization response URL with HTTPS
        authorization_response = str(request.url).replace("http://", "https://", 1)
        
        # Exchange code for credentials
        credentials = calendar_auth.handle_callback(authorization_response, state)
        
        return {
            "message": "Authentication successful! Your calendar is now connected.",
            "status": "success",
            "expires_at": credentials.expiry.isoformat() if credentials.expiry else None
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")


@app.get("/auth/status")
async def auth_status():
    """Check authentication status."""
    try:
        is_authenticated = calendar_auth.is_authenticated()
        
        return {
            "authenticated": is_authenticated,
            "calendar_id": settings.google_calendar_id if is_authenticated else None,
            "message": "Connected to Google Calendar" if is_authenticated else "Not authenticated"
        }
    except Exception as e:
        return {
            "authenticated": False,
            "error": str(e),
            "message": "Authentication check failed"
        }



@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPException",
            "message": exc.detail,
            "details": {"status_code": exc.status_code},
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": type(exc).__name__,
            "message": str(exc),
            "details": {"path": str(request.url)},
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.api.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True if settings.app_env == "development" else False
    )