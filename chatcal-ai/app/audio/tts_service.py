"""Text-to-Speech service using cloud providers."""

import asyncio
import base64
import io
import logging
from typing import AsyncGenerator, Optional
from abc import ABC, abstractmethod

from app.config import settings
from app.audio.models import AudioConfig, SpeechStartEvent, SpeechChunkEvent, SpeechEndEvent

logger = logging.getLogger(__name__)


class BaseTTSService(ABC):
    """Base class for Text-to-Speech services."""
    
    def __init__(self, config: AudioConfig):
        self.config = config
    
    @abstractmethod
    async def synthesize_stream(
        self, 
        text: str, 
        voice_id: Optional[str] = None
    ) -> AsyncGenerator[SpeechChunkEvent, None]:
        """Synthesize speech from text and stream audio chunks."""
        pass
    
    @abstractmethod
    async def synthesize_complete(
        self, 
        text: str, 
        voice_id: Optional[str] = None
    ) -> Optional[bytes]:
        """Synthesize complete audio file from text."""
        pass


class GoogleTTSService(BaseTTSService):
    """Google Cloud Text-to-Speech service."""
    
    def __init__(self, config: AudioConfig):
        super().__init__(config)
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Cloud TTS client."""
        try:
            from google.cloud import texttospeech
            from google.oauth2 import service_account
            
            # Use service account credentials if available
            if hasattr(settings, 'google_cloud_credentials_path'):
                credentials = service_account.Credentials.from_service_account_file(
                    settings.google_cloud_credentials_path
                )
                self.client = texttospeech.TextToSpeechClient(credentials=credentials)
            else:
                self.client = texttospeech.TextToSpeechClient()
                
            logger.info("Google TTS Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google TTS service: {e}")
            self.client = None
    
    async def synthesize_stream(
        self, 
        text: str, 
        voice_id: Optional[str] = None
    ) -> AsyncGenerator[SpeechChunkEvent, None]:
        """Synthesize speech and stream in chunks."""
        if not self.client:
            logger.error("Google TTS client not initialized")
            return
            
        try:
            from google.cloud import texttospeech
            
            # Configure synthesis
            input_text = texttospeech.SynthesisInput(text=text)
            
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name=voice_id or "en-US-Standard-J",  # Default to friendly female voice
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.OGG_OPUS,
                sample_rate_hertz=self.config.sample_rate
            )
            
            # Synthesize audio
            response = await asyncio.to_thread(
                self.client.synthesize_speech,
                input=input_text,
                voice=voice,
                audio_config=audio_config
            )
            
            # Stream audio in chunks
            audio_data = response.audio_content
            chunk_size = 4096  # 4KB chunks
            sequence = 0
            
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                encoded_chunk = base64.b64encode(chunk).decode('utf-8')
                
                yield SpeechChunkEvent(
                    audio_data=encoded_chunk,
                    sequence=sequence
                )
                sequence += 1
                
                # Small delay to simulate streaming
                await asyncio.sleep(0.05)
                
        except Exception as e:
            logger.error(f"Google TTS synthesis error: {e}")
    
    async def synthesize_complete(
        self, 
        text: str, 
        voice_id: Optional[str] = None
    ) -> Optional[bytes]:
        """Synthesize complete audio file."""
        if not self.client:
            return None
            
        try:
            from google.cloud import texttospeech
            
            input_text = texttospeech.SynthesisInput(text=text)
            
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name=voice_id or "en-US-Standard-J",
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.OGG_OPUS,
                sample_rate_hertz=self.config.sample_rate
            )
            
            response = await asyncio.to_thread(
                self.client.synthesize_speech,
                input=input_text,
                voice=voice,
                audio_config=audio_config
            )
            
            return response.audio_content
            
        except Exception as e:
            logger.error(f"Google TTS complete synthesis error: {e}")
            return None


class ElevenLabsTTSService(BaseTTSService):
    """ElevenLabs Text-to-Speech service."""
    
    def __init__(self, config: AudioConfig):
        super().__init__(config)
        self.api_key = getattr(settings, 'elevenlabs_api_key', None)
        self.base_url = "https://api.elevenlabs.io/v1"
        
        if not self.api_key:
            logger.warning("ElevenLabs API key not configured")
    
    async def synthesize_stream(
        self, 
        text: str, 
        voice_id: Optional[str] = None
    ) -> AsyncGenerator[SpeechChunkEvent, None]:
        """Synthesize speech using ElevenLabs streaming API."""
        if not self.api_key:
            logger.error("ElevenLabs API key not configured")
            return
            
        try:
            import aiohttp
            
            voice_id = voice_id or "21m00Tcm4TlvDq8ikWAM"  # Default voice
            url = f"{self.base_url}/text-to-speech/{voice_id}/stream"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        sequence = 0
                        async for chunk in response.content.iter_chunked(4096):
                            encoded_chunk = base64.b64encode(chunk).decode('utf-8')
                            
                            yield SpeechChunkEvent(
                                audio_data=encoded_chunk,
                                sequence=sequence
                            )
                            sequence += 1
                    else:
                        logger.error(f"ElevenLabs API error: {response.status}")
                        
        except Exception as e:
            logger.error(f"ElevenLabs synthesis error: {e}")
    
    async def synthesize_complete(
        self, 
        text: str, 
        voice_id: Optional[str] = None
    ) -> Optional[bytes]:
        """Synthesize complete audio file."""
        if not self.api_key:
            return None
            
        try:
            import aiohttp
            
            voice_id = voice_id or "21m00Tcm4TlvDq8ikWAM"
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        logger.error(f"ElevenLabs API error: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"ElevenLabs complete synthesis error: {e}")
            return None


class MockTTSService(BaseTTSService):
    """Mock TTS service for development/testing."""
    
    def __init__(self, config: AudioConfig):
        super().__init__(config)
        logger.info("Mock TTS Service initialized")
    
    async def synthesize_stream(
        self, 
        text: str, 
        voice_id: Optional[str] = None
    ) -> AsyncGenerator[SpeechChunkEvent, None]:
        """Mock synthesis that returns dummy audio chunks."""
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        # Generate dummy audio chunks
        for i in range(5):
            dummy_audio = b"dummy_audio_chunk_" + str(i).encode()
            encoded_chunk = base64.b64encode(dummy_audio).decode('utf-8')
            
            yield SpeechChunkEvent(
                audio_data=encoded_chunk,
                sequence=i
            )
            
            await asyncio.sleep(0.2)  # Simulate streaming delay
    
    async def synthesize_complete(
        self, 
        text: str, 
        voice_id: Optional[str] = None
    ) -> Optional[bytes]:
        """Mock complete synthesis."""
        await asyncio.sleep(0.5)
        return f"mock_audio_for: {text}".encode()


# Factory function to create TTS service based on configuration
def create_tts_service(config: AudioConfig, provider: str = "mock") -> BaseTTSService:
    """Create TTS service based on provider."""
    if provider == "google":
        return GoogleTTSService(config)
    elif provider == "elevenlabs":
        return ElevenLabsTTSService(config)
    else:
        return MockTTSService(config)