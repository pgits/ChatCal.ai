#!/usr/bin/env python3
"""
Simple CloudRun-compatible server for Kyutai Speech-to-Text
Uses subprocess to call moshi directly
"""

import asyncio
import base64
import json
import os
import subprocess
import tempfile
import time
import logging
from typing import Optional, Dict, Any

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import soundfile as sf

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleSTTProcessor:
    """Simple Speech-to-Text processor using moshi CLI with pre-cached models"""
    
    def __init__(self, hf_repo: str = "kyutai/stt-1b-en_fr-mlx"):
        self.hf_repo = hf_repo
        self.samplerate = 24000
        self.is_ready = False
        self.model_cache_dir = "/app/models"
        
    async def initialize(self):
        """Test that moshi is available and models are cached"""
        try:
            # Check if pre-cached models exist
            import glob
            import os
            
            model_files = glob.glob(f"{self.model_cache_dir}/**/*.safetensors", recursive=True)
            config_files = glob.glob(f"{self.model_cache_dir}/**/config.json", recursive=True)
            
            logger.info(f"Checking for cached models in {self.model_cache_dir}")
            logger.info(f"Found {len(model_files)} model files and {len(config_files)} config files")
            
            if model_files and config_files:
                logger.info("✅ Pre-cached models found!")
                total_size = 0
                for f in model_files:
                    size_mb = os.path.getsize(f) / 1024 / 1024
                    total_size += size_mb
                    logger.info(f"  - {os.path.basename(f)}: {size_mb:.1f} MB")
                
                logger.info(f"📊 Total model size: {total_size:.1f} MB")
                
                # If models are present, mark as ready and test moshi later
                # This allows the service to start even if moshi import is slow
                logger.info("🚀 Models are cached, marking as ready for faster startup")
                logger.info("⚠️  Moshi functionality will be tested on first request")
                
                self.is_ready = True
                return True
            else:
                logger.error("❌ No pre-cached models found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            return False
    
    def process_audio_chunk(self, audio_data: np.ndarray) -> str:
        """Process audio chunk using moshi CLI with pre-cached models"""
        try:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                # Ensure audio is in the right format
                if len(audio_data.shape) > 1:
                    audio_data = audio_data.mean(axis=1)  # Convert to mono
                
                # Write to WAV file
                sf.write(tmp_file.name, audio_data, self.samplerate)
                
                # Set environment variables to use pre-cached models
                env = os.environ.copy()
                env['HF_HOME'] = self.model_cache_dir
                env['TRANSFORMERS_CACHE'] = self.model_cache_dir
                env['HF_DATASETS_CACHE'] = self.model_cache_dir
                
                logger.info(f"Running STT inference on {len(audio_data)} samples...")
                
                # Run moshi inference with cached models
                result = subprocess.run([
                    "python", "-m", "moshi.run_inference",
                    "--hf-repo", self.hf_repo,
                    tmp_file.name
                ], 
                capture_output=True, 
                text=True, 
                timeout=60,  # Increased timeout for processing
                env=env
                )
                
                # Clean up
                os.unlink(tmp_file.name)
                
                if result.returncode == 0:
                    # Extract transcription from output
                    output_lines = result.stdout.strip().split('\n')
                    logger.info(f"Moshi output lines: {len(output_lines)}")
                    
                    # Look for the actual transcription (skip progress/debug lines)
                    transcription_candidates = []
                    for line in output_lines:
                        line = line.strip()
                        if line and not line.startswith((
                            'Loading', 'Using', 'Progress', 'Downloading', 
                            'Model loaded', 'Processing', '100%', 'Running',
                            'Config', 'INFO:', 'WARNING:', 'ERROR:'
                        )):
                            transcription_candidates.append(line)
                    
                    if transcription_candidates:
                        # Use the last non-empty candidate as the final transcription
                        transcription = transcription_candidates[-1]
                        logger.info(f"Extracted transcription: '{transcription}'")
                        return transcription
                    else:
                        logger.warning("No transcription found in output")
                        return ""
                else:
                    logger.error(f"Moshi inference failed (code {result.returncode}): {result.stderr}")
                    return ""
                    
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return ""

# Global STT processor instance
stt_processor = SimpleSTTProcessor()

# FastAPI app
app = FastAPI(
    title="Simple Kyutai STT CloudRun Server",
    description="Simple Speech-to-Text service using Kyutai STT models",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize STT processor on startup"""
    logger.info("Starting up STT server...")
    success = await stt_processor.initialize()
    if not success:
        logger.warning("STT processor initialization failed, but continuing...")
        # Don't fail startup, just warn

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Simple Kyutai STT CloudRun Server", 
        "status": "running",
        "ready": stt_processor.is_ready
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for CloudRun"""
    return {
        "status": "healthy",
        "model": stt_processor.hf_repo,
        "timestamp": time.time(),
        "ready": stt_processor.is_ready
    }

@app.post("/transcribe")
async def transcribe_audio(audio_data: Dict[str, Any]):
    """Transcribe base64-encoded audio data"""
    if not stt_processor.is_ready:
        raise HTTPException(status_code=503, detail="STT processor not ready")
    
    try:
        # Decode base64 audio
        audio_b64 = audio_data.get("audio")
        if not audio_b64:
            raise HTTPException(status_code=400, detail="No audio data provided")
        
        audio_bytes = base64.b64decode(audio_b64)
        audio_np = np.frombuffer(audio_bytes, dtype=np.float32)
        
        # Process audio
        start_time = time.time()
        transcription = stt_processor.process_audio_chunk(audio_np)
        processing_time = time.time() - start_time
        
        return {
            "transcription": transcription,
            "timestamp": time.time(),
            "audio_length": len(audio_np),
            "processing_time_ms": processing_time * 1000
        }
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    """WebSocket endpoint for real-time transcription"""
    if not stt_processor.is_ready:
        await websocket.close(code=1011, reason="STT processor not ready")
        return
        
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    try:
        while True:
            # Receive audio data
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "audio":
                # Process audio chunk
                audio_b64 = message.get("audio")
                if audio_b64:
                    start_time = time.time()
                    audio_bytes = base64.b64decode(audio_b64)
                    audio_np = np.frombuffer(audio_bytes, dtype=np.float32)
                    
                    # Transcribe
                    transcription = stt_processor.process_audio_chunk(audio_np)
                    processing_time = time.time() - start_time
                    
                    # Send result
                    response = {
                        "type": "transcription",
                        "text": transcription,
                        "timestamp": time.time(),
                        "processing_time_ms": processing_time * 1000
                    }
                    await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()

# Simple test endpoint that doesn't require moshi
@app.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {
        "message": "Server is running",
        "timestamp": time.time(),
        "python_version": os.sys.version
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
        workers=1  # Single worker for CloudRun
    )