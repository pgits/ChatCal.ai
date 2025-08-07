"""Speech-to-Text service using Google Cloud Speech API."""

import asyncio
import base64
import io
import logging
from typing import AsyncGenerator, Optional

from google.cloud import speech
from google.oauth2 import service_account
import webrtcvad

from app.config import settings
from app.audio.models import AudioConfig, TranscriptionPartialEvent, TranscriptionFinalEvent

logger = logging.getLogger(__name__)


class STTService:
    """Speech-to-Text service using Google Cloud Speech API."""
    
    def __init__(self, config: AudioConfig):
        self.config = config
        self.client: Optional[speech.SpeechClient] = None
        self.vad: Optional[webrtcvad.Vad] = None
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize Google Cloud Speech client."""
        try:
            # Use service account credentials if available
            if hasattr(settings, 'google_cloud_credentials_path'):
                credentials = service_account.Credentials.from_service_account_file(
                    settings.google_cloud_credentials_path
                )
                self.client = speech.SpeechClient(credentials=credentials)
            else:
                # Use default credentials (environment variable or metadata service)
                self.client = speech.SpeechClient()
                
            # Initialize Voice Activity Detection
            if self.config.enable_vad:
                self.vad = webrtcvad.Vad(2)  # Aggressiveness level 0-3
                
            logger.info("STT Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize STT service: {e}")
            self.client = None
    
    async def transcribe_stream(
        self, 
        audio_stream: AsyncGenerator[bytes, None]
    ) -> AsyncGenerator[TranscriptionPartialEvent | TranscriptionFinalEvent, None]:
        """Transcribe streaming audio data."""
        if not self.client:
            logger.error("STT client not initialized")
            return
            
        try:
            # Configure recognition
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                sample_rate_hertz=self.config.sample_rate,
                language_code="en-US",
                enable_automatic_punctuation=True,
                enable_word_time_offsets=False,
                model="latest_long",  # Use latest model for best accuracy
            )
            
            streaming_config = speech.StreamingRecognitionConfig(
                config=config,
                interim_results=True,  # Enable partial results
                single_utterance=False,
            )
            
            # Create audio generator for the API
            async def audio_generator():
                async for chunk in audio_stream:
                    # Apply voice activity detection if enabled
                    if self.vad and self._is_speech(chunk):
                        yield speech.StreamingRecognizeRequest(audio_content=chunk)
                    elif not self.vad:
                        yield speech.StreamingRecognizeRequest(audio_content=chunk)
            
            # Initial request with config
            yield speech.StreamingRecognizeRequest(streaming_config=streaming_config)
            
            # Process audio chunks
            requests = audio_generator()
            responses = self.client.streaming_recognize(requests)
            
            for response in responses:
                if response.results:
                    result = response.results[0]
                    if result.alternatives:
                        transcript = result.alternatives[0].transcript
                        confidence = result.alternatives[0].confidence
                        
                        if result.is_final:
                            yield TranscriptionFinalEvent(
                                text=transcript,
                                confidence=confidence
                            )
                        else:
                            yield TranscriptionPartialEvent(
                                text=transcript,
                                confidence=confidence
                            )
                            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            
    def _is_speech(self, audio_chunk: bytes, chunk_duration_ms: int = 20) -> bool:
        """Use Voice Activity Detection to determine if audio contains speech."""
        if not self.vad:
            return True
            
        try:
            # VAD expects 16-bit PCM audio
            # This is a simplified implementation - you'd need proper audio conversion
            return self.vad.is_speech(audio_chunk, self.config.sample_rate)
        except Exception as e:
            logger.warning(f"VAD error: {e}")
            return True  # Default to assuming speech
    
    async def transcribe_file(self, audio_data: bytes) -> Optional[str]:
        """Transcribe a complete audio file."""
        if not self.client:
            logger.error("STT client not initialized")
            return None
            
        try:
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                sample_rate_hertz=self.config.sample_rate,
                language_code="en-US",
                enable_automatic_punctuation=True,
            )
            
            audio = speech.RecognitionAudio(content=audio_data)
            response = self.client.recognize(config=config, audio=audio)
            
            if response.results:
                return response.results[0].alternatives[0].transcript
            return None
            
        except Exception as e:
            logger.error(f"File transcription error: {e}")
            return None


class MockSTTService(STTService):
    """Mock STT service for development/testing."""
    
    def __init__(self, config: AudioConfig):
        self.config = config
        logger.info("Mock STT Service initialized")
    
    async def transcribe_stream(
        self, 
        audio_stream: AsyncGenerator[bytes, None]
    ) -> AsyncGenerator[TranscriptionPartialEvent | TranscriptionFinalEvent, None]:
        """Mock transcription that returns dummy results."""
        await asyncio.sleep(1)  # Simulate processing delay
        
        yield TranscriptionPartialEvent(
            text="I would like to schedule",
            confidence=0.8
        )
        
        await asyncio.sleep(1)
        
        yield TranscriptionFinalEvent(
            text="I would like to schedule a meeting with Peter tomorrow at 2 PM",
            confidence=0.95
        )
    
    async def transcribe_file(self, audio_data: bytes) -> Optional[str]:
        """Mock file transcription."""
        await asyncio.sleep(0.5)
        return "I would like to schedule a meeting with Peter tomorrow at 2 PM"