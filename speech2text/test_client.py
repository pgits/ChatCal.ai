#!/usr/bin/env python3
"""
Test client for Kyutai STT CloudRun service
Supports both REST API and WebSocket connections
"""

import asyncio
import base64
import json
import ssl
import time
import numpy as np
import requests
import websockets
import sounddevice as sd
import certifi
from typing import Optional

class STTClient:
    """Client for testing CloudRun STT service"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.ws_url = base_url.replace('https://', 'wss://').replace('http://', 'ws://')
    
    def test_health(self):
        """Test health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Health check failed: {e}")
            return None
    
    def transcribe_audio_file(self, audio_path: str):
        """Transcribe audio from file using REST API"""
        try:
            # For this example, generate dummy audio data
            # In practice, you'd load and convert your audio file
            duration = 2.0  # seconds
            samplerate = 24000
            samples = int(duration * samplerate)
            
            # Generate test audio (sine wave)
            t = np.linspace(0, duration, samples)
            audio_data = np.sin(2 * np.pi * 440 * t).astype(np.float32)  # 440Hz tone
            
            # Encode to base64
            audio_bytes = audio_data.tobytes()
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            # Send to API
            payload = {"audio": audio_b64}
            response = requests.post(
                f"{self.base_url}/transcribe", 
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"Transcription failed: {e}")
            return None
    
    def create_ssl_context(self, strategy: str = "auto"):
        """Create SSL context with different strategies"""
        try:
            if strategy == "secure":
                # Production-grade SSL with full verification
                context = ssl.create_default_context()
                context.check_hostname = True
                context.verify_mode = ssl.CERT_REQUIRED
                context.load_verify_locations(certifi.where())
                return context
            elif strategy == "relaxed":
                # Relaxed SSL for CloudRun (no hostname verification)
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_REQUIRED
                context.load_verify_locations(certifi.where())
                return context
            elif strategy == "unverified":
                # Unverified SSL (development only)
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                return context
            else:
                # Auto-detect best strategy
                return None
        except Exception as e:
            print(f"Warning: SSL context creation failed: {e}")
            return None

    async def connect_websocket(self, uri: str):
        """Connect to WebSocket with SSL fallback strategies"""
        strategies = [
            ("secure", "Secure SSL with full verification"),
            ("relaxed", "Relaxed SSL (CloudRun compatible)"),
            ("unverified", "Unverified SSL (development only)")
        ]
        
        for strategy_name, description in strategies:
            try:
                print(f"🔐 Trying {description}...")
                ssl_context = self.create_ssl_context(strategy_name)
                
                websocket = await websockets.connect(
                    uri, 
                    ssl=ssl_context,
                    ping_interval=20,
                    ping_timeout=10
                )
                
                print(f"✅ Connected using {description}")
                return websocket
                
            except ssl.SSLError as e:
                print(f"❌ {strategy_name} SSL failed: {e}")
            except Exception as e:
                print(f"❌ {strategy_name} failed: {type(e).__name__}: {e}")
        
        raise ConnectionError("All SSL strategies failed")

    async def test_websocket(self, duration: float = 5.0):
        """Test real-time transcription via WebSocket"""
        try:
            uri = f"{self.ws_url}/ws/transcribe"
            print(f"Connecting to WebSocket: {uri}")
            
            websocket = await self.connect_websocket(uri)
            
            async with websocket:
                print("WebSocket connected, sending test audio...")
                
                # Send test audio chunks
                samplerate = 24000
                chunk_duration = 0.1  # 100ms chunks
                chunk_samples = int(chunk_duration * samplerate)
                
                for i in range(int(duration / chunk_duration)):
                    # Generate test audio chunk
                    t = np.linspace(
                        i * chunk_duration, 
                        (i + 1) * chunk_duration, 
                        chunk_samples
                    )
                    audio_chunk = np.sin(2 * np.pi * 440 * t).astype(np.float32)
                    
                    # Encode and send
                    audio_bytes = audio_chunk.tobytes()
                    audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                    
                    message = {
                        "type": "audio",
                        "audio": audio_b64
                    }
                    
                    await websocket.send(json.dumps(message))
                    
                    # Try to receive response (non-blocking)
                    try:
                        response = await asyncio.wait_for(
                            websocket.recv(), 
                            timeout=0.1
                        )
                        result = json.loads(response)
                        if result.get('text'):
                            print(f"Transcription: {result['text']}")
                            print(f"Processing time: {result.get('processing_time_ms', 0):.1f}ms")
                    except asyncio.TimeoutError:
                        pass
                    
                    await asyncio.sleep(chunk_duration)
                
                print("WebSocket test completed")
                
        except Exception as e:
            print(f"WebSocket test failed: {e}")
    
    async def test_microphone(self, duration: float = 10.0):
        """Test real-time transcription from microphone"""
        try:
            uri = f"{self.ws_url}/ws/transcribe"
            print(f"Connecting to WebSocket for microphone test: {uri}")
            
            # Audio parameters
            samplerate = 24000
            blocksize = int(0.1 * samplerate)  # 100ms blocks
            
            websocket = await self.connect_websocket(uri)
            
            async with websocket:
                print(f"🎤 Recording from microphone for {duration} seconds...")
                print("Speak into your microphone!")
                
                # Audio callback to capture and send audio
                audio_queue = asyncio.Queue()
                
                def audio_callback(indata, frames, time, status):
                    if status:
                        print(f"Audio status: {status}")
                    # Convert to mono and queue
                    mono_audio = indata[:, 0] if indata.shape[1] > 1 else indata.flatten()
                    asyncio.create_task(audio_queue.put(mono_audio.copy()))
                
                # Start audio stream
                stream = sd.InputStream(
                    channels=1,
                    samplerate=samplerate,
                    blocksize=blocksize,
                    dtype=np.float32,
                    callback=audio_callback
                )
                
                with stream:
                    start_time = time.time()
                    
                    while time.time() - start_time < duration:
                        try:
                            # Get audio data
                            audio_chunk = await asyncio.wait_for(
                                audio_queue.get(), 
                                timeout=0.5
                            )
                            
                            # Send to server
                            audio_bytes = audio_chunk.tobytes()
                            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                            
                            message = {
                                "type": "audio",
                                "audio": audio_b64
                            }
                            
                            await websocket.send(json.dumps(message))
                            
                            # Try to receive response
                            try:
                                response = await asyncio.wait_for(
                                    websocket.recv(), 
                                    timeout=0.05
                                )
                                result = json.loads(response)
                                if result.get('text'):
                                    print(f"📝 {result['text']}", end="", flush=True)
                            except asyncio.TimeoutError:
                                pass
                                
                        except asyncio.TimeoutError:
                            continue
                
                print("\n🛑 Microphone test completed")
                
        except Exception as e:
            print(f"Microphone test failed: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Kyutai STT CloudRun service")
    parser.add_argument("--url", required=True, help="CloudRun service URL")
    parser.add_argument("--test", choices=["health", "file", "websocket", "microphone", "all"], 
                       default="all", help="Test to run")
    parser.add_argument("--duration", type=float, default=5.0, 
                       help="Duration for streaming tests")
    
    args = parser.parse_args()
    
    client = STTClient(args.url)
    
    print(f"Testing STT service: {args.url}")
    
    if args.test in ["health", "all"]:
        print("\n🩺 Testing health endpoint...")
        health = client.test_health()
        if health:
            print(f"✅ Health check passed: {health}")
        else:
            print("❌ Health check failed")
    
    if args.test in ["file", "all"]:
        print("\n📁 Testing file transcription...")
        result = client.transcribe_audio_file("dummy.wav")
        if result:
            print(f"✅ File transcription: {result}")
        else:
            print("❌ File transcription failed")
    
    if args.test in ["websocket", "all"]:
        print(f"\n🌐 Testing WebSocket with synthetic audio ({args.duration}s)...")
        asyncio.run(client.test_websocket(args.duration))
    
    if args.test in ["microphone", "all"]:
        print(f"\n🎤 Testing microphone input ({args.duration}s)...")
        asyncio.run(client.test_microphone(args.duration))

if __name__ == "__main__":
    main()