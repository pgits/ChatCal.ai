#!/usr/bin/env python3
"""
CloudRun-compatible server for Kyutai Speech-to-Text
CPU-only version for cost-effective deployment
"""

import asyncio
import base64
import json
import os
import time
import logging
from typing import Optional, Dict, Any

import numpy as np
import torch
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import Kyutai STT components
try:
    from moshi.models import LmConfig, Lm
    from moshi import utils
    import sentencepiece
    from huggingface_hub import hf_hub_download
except ImportError as e:
    logging.error(f"Failed to import moshi components: {e}")
    logging.error("Install with: pip install moshi>=0.2.6")
    raise

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class STTProcessor:
    """Speech-to-Text processor using Kyutai STT models"""
    
    def __init__(self, hf_repo: str = "kyutai/stt-1b-en_fr"):
        self.hf_repo = hf_repo
        self.model = None
        self.text_tokenizer = None
        self.gen = None
        self.samplerate = 24000
        self.block_size = 1920
        
    async def initialize(self):
        """Initialize the STT model"""
        logger.info(f"Initializing STT model: {self.hf_repo}")
        
        try:
            # Download model files
            lm_config_path = hf_hub_download(self.hf_repo, "config.json")
            with open(lm_config_path, "r") as f:
                lm_config = json.load(f)
            
            # Download weights and tokenizer
            moshi_weights = hf_hub_download(
                self.hf_repo, 
                lm_config.get("moshi_name", "model.safetensors")
            )
            tokenizer_path = hf_hub_download(
                self.hf_repo, 
                lm_config["tokenizer_name"]
            )
            
            # Initialize model
            lm_config = LmConfig.from_config_dict(lm_config)
            self.model = Lm(lm_config)
            self.model.load_state_dict(torch.load(moshi_weights, map_location="cpu"))
            self.model.eval()
            
            # Initialize tokenizer
            self.text_tokenizer = sentencepiece.SentencePieceProcessor(tokenizer_path)
            
            # Setup generation
            self.gen = utils.LmGen(
                model=self.model,
                max_steps=4096,
                text_sampler=utils.Sampler(top_k=25, temp=0),
                audio_sampler=utils.Sampler(top_k=250, temp=0.8),
            )
            
            logger.info("STT model initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize STT model: {e}")
            return False
    
    def process_audio_chunk(self, audio_data: np.ndarray) -> str:
        """Process a chunk of audio data and return transcription"""
        try:
            # Ensure audio is in the right format
            if len(audio_data.shape) > 1:
                audio_data = audio_data.mean(axis=1)  # Convert to mono
            
            # Resample if needed (basic linear interpolation)
            if len(audio_data) != self.block_size:
                audio_data = np.interp(
                    np.linspace(0, len(audio_data), self.block_size),
                    np.arange(len(audio_data)),
                    audio_data
                )
            
            # Convert to tensor
            audio_tensor = torch.from_numpy(audio_data).float().unsqueeze(0)
            
            # Process through model (simplified version)
            with torch.no_grad():
                # This is a simplified version - in production you'd need
                # the full audio tokenizer pipeline
                text_tokens = self.model.forward(audio_tensor)
                
                # Decode text tokens
                if hasattr(text_tokens, 'argmax'):
                    token_ids = text_tokens.argmax(dim=-1).tolist()
                    transcription = self.text_tokenizer.decode(token_ids)
                    return transcription.strip()
            
            return ""
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            return ""

# Global STT processor instance
stt_processor = STTProcessor()

# FastAPI app
app = FastAPI(
    title="Kyutai STT CloudRun Server",
    description="Speech-to-Text service using Kyutai STT models",
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
    success = await stt_processor.initialize()
    if not success:
        logger.error("Failed to initialize STT processor")
        raise HTTPException(status_code=500, detail="STT initialization failed")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Kyutai STT CloudRun Server", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint for CloudRun"""
    return {
        "status": "healthy",
        "model": stt_processor.hf_repo,
        "timestamp": time.time()
    }

@app.post("/transcribe")
async def transcribe_audio(audio_data: Dict[str, Any]):
    """Transcribe base64-encoded audio data"""
    try:
        # Decode base64 audio
        audio_b64 = audio_data.get("audio")
        if not audio_b64:
            raise HTTPException(status_code=400, detail="No audio data provided")
        
        audio_bytes = base64.b64decode(audio_b64)
        audio_np = np.frombuffer(audio_bytes, dtype=np.float32)
        
        # Process audio
        transcription = stt_processor.process_audio_chunk(audio_np)
        
        return {
            "transcription": transcription,
            "timestamp": time.time(),
            "audio_length": len(audio_np)
        }
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    """WebSocket endpoint for real-time transcription"""
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
                    audio_bytes = base64.b64decode(audio_b64)
                    audio_np = np.frombuffer(audio_bytes, dtype=np.float32)
                    
                    # Transcribe
                    transcription = stt_processor.process_audio_chunk(audio_np)
                    
                    # Send result
                    if transcription:
                        response = {
                            "type": "transcription",
                            "text": transcription,
                            "timestamp": time.time()
                        }
                        await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()

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