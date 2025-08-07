"""Pydantic models for API requests and responses."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User message to the chatbot", min_length=1, max_length=1000)
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    stream: bool = Field(False, description="Whether to stream the response")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str = Field(..., description="Chatbot response")
    session_id: str = Field(..., description="Session ID")
    timestamp: datetime = Field(..., description="Response timestamp")
    tools_used: Optional[List[str]] = Field(None, description="List of tools used in response")


class StreamChatResponse(BaseModel):
    """Response model for streaming chat."""
    token: str = Field(..., description="Response token")
    session_id: str = Field(..., description="Session ID")
    is_complete: bool = Field(False, description="Whether this is the final token")


class SessionCreate(BaseModel):
    """Request model for creating a new session."""
    user_data: Optional[Dict[str, Any]] = Field(None, description="Optional user data")


class SessionResponse(BaseModel):
    """Response model for session operations."""
    session_id: str = Field(..., description="Session ID")
    created_at: datetime = Field(..., description="Session creation timestamp")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    is_active: bool = Field(..., description="Whether session is active")


class ConversationHistory(BaseModel):
    """Model for conversation history."""
    session_id: str = Field(..., description="Session ID")
    messages: List[Dict[str, Any]] = Field(..., description="List of conversation messages")
    created_at: datetime = Field(..., description="Conversation start timestamp")


class CalendarEvent(BaseModel):
    """Model for calendar events."""
    id: Optional[str] = Field(None, description="Event ID")
    summary: str = Field(..., description="Event title/summary")
    start_time: datetime = Field(..., description="Event start time")
    end_time: datetime = Field(..., description="Event end time")
    description: Optional[str] = Field(None, description="Event description")
    location: Optional[str] = Field(None, description="Event location")
    attendees: Optional[List[str]] = Field(None, description="List of attendee emails")


class AvailabilityRequest(BaseModel):
    """Request model for checking availability."""
    date: str = Field(..., description="Date in natural language (e.g., 'next Tuesday')")
    duration_minutes: int = Field(60, description="Meeting duration in minutes", ge=15, le=480)
    preferred_time: Optional[str] = Field(None, description="Preferred time (e.g., '2pm', 'morning')")


class AvailabilityResponse(BaseModel):
    """Response model for availability check."""
    date: str = Field(..., description="Formatted date")
    available_slots: List[Dict[str, str]] = Field(..., description="List of available time slots")
    duration_minutes: int = Field(..., description="Requested duration")


class AppointmentRequest(BaseModel):
    """Request model for creating appointments."""
    title: str = Field(..., description="Meeting title", min_length=1, max_length=200)
    date: str = Field(..., description="Date in natural language")
    time: str = Field(..., description="Time in natural language")
    duration_minutes: int = Field(60, description="Duration in minutes", ge=15, le=480)
    description: Optional[str] = Field(None, description="Meeting description", max_length=1000)
    attendees: Optional[List[str]] = Field(None, description="List of attendee emails")


class AppointmentResponse(BaseModel):
    """Response model for appointment operations."""
    success: bool = Field(..., description="Whether operation was successful")
    message: str = Field(..., description="Success or error message")
    event: Optional[CalendarEvent] = Field(None, description="Created/updated event details")


class AuthRequest(BaseModel):
    """Request model for authentication."""
    state: Optional[str] = Field(None, description="OAuth state parameter")


class AuthResponse(BaseModel):
    """Response model for authentication."""
    auth_url: str = Field(..., description="Google OAuth authorization URL")
    state: str = Field(..., description="OAuth state parameter")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(..., description="Health check timestamp")
    services: Dict[str, str] = Field(..., description="Status of dependent services")


class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(..., description="Error timestamp")


class VersionResponse(BaseModel):
    """Version response model."""
    app_version: str = Field(..., description="Application semantic version")
    git_commit: str = Field(..., description="Git commit hash")
    git_branch: str = Field(..., description="Git branch name")
    build_timestamp: datetime = Field(..., description="Build timestamp")
    environment: str = Field(..., description="Environment (development/production)")
    python_version: str = Field(..., description="Python version")
    healthy: bool = Field(..., description="Service health status")