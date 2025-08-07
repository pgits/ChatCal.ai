"""WebSocket handler for audio chat functionality."""

import asyncio
import base64
import json
import logging
from typing import Dict, Optional

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from app.audio.models import (
    AudioEvent, AudioEventType, AudioStartEvent, AudioChunkEvent, AudioEndEvent,
    TranscriptionPartialEvent, TranscriptionFinalEvent,
    SpeechStartEvent, SpeechChunkEvent, SpeechEndEvent,
    AudioErrorEvent, AudioStatusEvent, AudioConfig
)
from app.audio.stt_service import STTService, MockSTTService
from app.audio.tts_service import create_tts_service
from app.core.session import session_manager

logger = logging.getLogger(__name__)


class AudioWebSocketHandler:
    """Handles WebSocket communication for audio chat."""
    
    def __init__(self, websocket: WebSocket, session_id: str):
        self.websocket = websocket
        self.session_id = session_id
        self.config = AudioConfig()
        
        # Initialize services
        self.stt_service = MockSTTService(self.config)  # Start with mock
        self.tts_service = create_tts_service(self.config, "mock")  # Start with mock
        
        # Audio processing state
        self.is_recording = False
        self.audio_buffer = bytearray()
        self.sequence_number = 0
        
        # Get or create conversation for this session
        self.conversation = session_manager.get_or_create_conversation(session_id)
    
    async def handle_connection(self):
        """Main handler for WebSocket connection."""
        try:
            await self.websocket.accept()
            logger.info(f"Audio WebSocket connected for session {self.session_id}")
            
            # Send initial status
            await self.send_event(AudioStatusEvent(
                status="connected",
                details={"session_id": self.session_id}
            ))
            
            # Start concurrent tasks for handling messages and processing
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self._receive_loop())
                
        except WebSocketDisconnect:
            logger.info(f"Audio WebSocket disconnected for session {self.session_id}")
        except Exception as e:
            logger.error(f"Audio WebSocket error: {e}")
            await self.send_error("Internal server error")
        finally:
            await self._cleanup()
    
    async def _receive_loop(self):
        """Main loop for receiving and processing WebSocket messages."""
        while True:
            try:
                # Check if WebSocket is still connected
                if (self.websocket.application_state == WebSocketState.DISCONNECTED or 
                    self.websocket.client_state == WebSocketState.DISCONNECTED):
                    break
                
                # Receive message from client
                data = await self.websocket.receive_text()
                event_data = json.loads(data)
                
                # Parse and handle event
                await self._handle_event(event_data)
                
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected during receive loop")
                break
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                await self.send_error("Invalid JSON format")
            except Exception as e:
                logger.error(f"Error in receive loop: {e}")
                await self.send_error("Processing error")
    
    async def _handle_event(self, event_data: Dict):
        """Handle incoming audio events."""
        try:
            event_type = event_data.get("type")
            
            if event_type == AudioEventType.AUDIO_START:
                await self._handle_audio_start(AudioStartEvent(**event_data))
            elif event_type == AudioEventType.AUDIO_CHUNK:
                await self._handle_audio_chunk(AudioChunkEvent(**event_data))
            elif event_type == AudioEventType.AUDIO_END:
                await self._handle_audio_end(AudioEndEvent(**event_data))
            else:
                logger.warning(f"Unknown event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Error handling event: {e}")
            await self.send_error(f"Event handling error: {str(e)}")
    
    async def _handle_audio_start(self, event: AudioStartEvent):
        """Handle start of audio recording."""
        logger.info(f"Audio recording started: {event.sample_rate}Hz, {event.channels} channels")
        
        self.is_recording = True
        self.audio_buffer.clear()
        self.sequence_number = 0
        
        # Send acknowledgment
        await self.send_event(AudioStatusEvent(
            status="recording",
            details={"sample_rate": event.sample_rate, "channels": event.channels}
        ))
    
    async def _handle_audio_chunk(self, event: AudioChunkEvent):
        """Handle incoming audio chunk."""
        if not self.is_recording:
            return
        
        try:
            # Decode base64 audio data
            audio_data = base64.b64decode(event.audio_data)
            self.audio_buffer.extend(audio_data)
            
            # Send partial transcription for real-time feedback
            # (In a real implementation, you'd stream this to STT service)
            if len(self.audio_buffer) > 8000:  # Arbitrary threshold
                await self.send_event(TranscriptionPartialEvent(
                    text="Listening...",
                    confidence=0.5
                ))
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            await self.send_error("Audio processing error")
    
    async def _handle_audio_end(self, event: AudioEndEvent):
        """Handle end of audio recording and process complete audio."""
        logger.info("Audio recording ended")
        
        self.is_recording = False
        
        if not self.audio_buffer:
            await self.send_error("No audio data received")
            return
        
        try:
            # Process complete audio for transcription
            audio_bytes = bytes(self.audio_buffer)
            
            # Use STT service to transcribe
            transcription = await self.stt_service.transcribe_file(audio_bytes)
            
            if transcription:
                # Send final transcription
                await self.send_event(TranscriptionFinalEvent(
                    text=transcription,
                    confidence=0.95
                ))
                
                # Process the transcription through the chat agent
                await self._process_transcription(transcription)
            else:
                await self.send_error("Could not transcribe audio")
                
        except Exception as e:
            logger.error(f"Error processing complete audio: {e}")
            await self.send_error("Transcription error")
        finally:
            self.audio_buffer.clear()
    
    async def _process_transcription(self, text: str):
        """Process transcribed text through the chat agent."""
        try:
            if not self.conversation:
                await self.send_error("No conversation session found")
                return
            
            # Get response from chat agent
            response = self.conversation.get_response(text)
            
            # Convert response to speech
            await self._synthesize_speech(response)
            
        except Exception as e:
            logger.error(f"Error processing transcription: {e}")
            await self.send_error("Chat processing error")
    
    async def _synthesize_speech(self, text: str):
        """Convert text response to speech and stream to client."""
        try:
            # Send speech start event
            await self.send_event(SpeechStartEvent(text=text))
            
            # Stream audio chunks from TTS service
            async for speech_chunk in self.tts_service.synthesize_stream(text):
                await self.send_event(speech_chunk)
            
            # Send speech end event
            await self.send_event(SpeechEndEvent())
            
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            await self.send_error("Speech synthesis error")
    
    async def send_event(self, event: AudioEvent):
        """Send an audio event to the client."""
        try:
            if (self.websocket.application_state != WebSocketState.DISCONNECTED and 
                self.websocket.client_state != WebSocketState.DISCONNECTED):
                
                event_data = event.model_dump()
                await self.websocket.send_text(json.dumps(event_data))
                
        except Exception as e:
            logger.error(f"Error sending event: {e}")
    
    async def send_error(self, message: str):
        """Send an error event to the client."""
        error_event = AudioErrorEvent(error=message)
        await self.send_event(error_event)
    
    async def _cleanup(self):
        """Clean up resources when connection closes."""
        self.is_recording = False
        self.audio_buffer.clear()
        logger.info(f"Audio WebSocket cleanup completed for session {self.session_id}")


# WebSocket endpoint function
async def audio_websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for audio chat."""
    handler = AudioWebSocketHandler(websocket, session_id)
    await handler.handle_connection()