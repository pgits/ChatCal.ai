"""Audio-related data models for voice chat functionality."""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AudioEventType(str, Enum):
    """Types of audio events in the WebSocket protocol."""
    # Client -> Server events
    AUDIO_START = "audio.start"
    AUDIO_CHUNK = "audio.chunk"
    AUDIO_END = "audio.end"
    
    # Server -> Client events
    TRANSCRIPTION_PARTIAL = "transcription.partial"
    TRANSCRIPTION_FINAL = "transcription.final"
    SPEECH_START = "speech.start"
    SPEECH_CHUNK = "speech.chunk"
    SPEECH_END = "speech.end"
    
    # System events
    ERROR = "error"
    STATUS = "status"


class AudioEvent(BaseModel):
    """Base class for all audio events."""
    type: AudioEventType
    timestamp: Optional[float] = None


class AudioStartEvent(AudioEvent):
    """Event indicating start of audio recording."""
    type: AudioEventType = AudioEventType.AUDIO_START
    sample_rate: int = 16000
    channels: int = 1
    format: str = "webm"


class AudioChunkEvent(AudioEvent):
    """Event containing audio data chunk."""
    type: AudioEventType = AudioEventType.AUDIO_CHUNK
    audio_data: str = Field(..., description="Base64-encoded audio data")
    sequence: int = Field(..., description="Sequence number for ordering")


class AudioEndEvent(AudioEvent):
    """Event indicating end of audio recording."""
    type: AudioEventType = AudioEventType.AUDIO_END


class TranscriptionPartialEvent(AudioEvent):
    """Partial transcription result."""
    type: AudioEventType = AudioEventType.TRANSCRIPTION_PARTIAL
    text: str
    confidence: Optional[float] = None


class TranscriptionFinalEvent(AudioEvent):
    """Final transcription result."""
    type: AudioEventType = AudioEventType.TRANSCRIPTION_FINAL
    text: str
    confidence: Optional[float] = None


class SpeechStartEvent(AudioEvent):
    """Event indicating start of TTS speech generation."""
    type: AudioEventType = AudioEventType.SPEECH_START
    text: str
    voice_id: Optional[str] = None


class SpeechChunkEvent(AudioEvent):
    """Event containing generated speech audio chunk."""
    type: AudioEventType = AudioEventType.SPEECH_CHUNK
    audio_data: str = Field(..., description="Base64-encoded audio data")
    sequence: int = Field(..., description="Sequence number for ordering")


class SpeechEndEvent(AudioEvent):
    """Event indicating end of TTS speech generation."""
    type: AudioEventType = AudioEventType.SPEECH_END


class AudioErrorEvent(AudioEvent):
    """Event indicating an audio processing error."""
    type: AudioEventType = AudioEventType.ERROR
    error: str
    details: Optional[Dict[str, Any]] = None


class AudioStatusEvent(AudioEvent):
    """Event containing status information."""
    type: AudioEventType = AudioEventType.STATUS
    status: str
    details: Optional[Dict[str, Any]] = None


# Configuration models
class AudioConfig(BaseModel):
    """Audio processing configuration."""
    sample_rate: int = 16000
    channels: int = 1
    chunk_duration_ms: int = 100
    enable_vad: bool = True  # Voice Activity Detection
    silence_threshold: float = 0.01
    speech_timeout_ms: int = 3000  # Auto-stop after silence