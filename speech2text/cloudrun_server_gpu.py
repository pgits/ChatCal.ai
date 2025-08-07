#!/usr/bin/env python3
"""
CloudRun-compatible server for Kyutai Speech-to-Text with GPU support
For deployment with GPU resources
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
    from moshi.models import LmConfig, Lm, mimi
    from moshi import utils
    import sentencepiece
    from huggingface_hub import hf_hub_download
    import rustymimi
except ImportError as e:
    logging.error(f"Failed to import moshi components: {e}")
    logging.error("Install with: pip install moshi>=0.2.6")
    raise

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class STTProcessorGPU:
    """GPU-accelerated Speech-to-Text processor using Kyutai STT models"""
    
    def __init__(self, hf_repo: str = "kyutai/stt-1b-en_fr"):
        self.hf_repo = hf_repo
        self.model = None
        self.text_tokenizer = None
        self.audio_tokenizer = None
        self.gen = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.samplerate = 24000
        self.block_size = 1920
        
    async def initialize(self):
        """Initialize the STT model with GPU acceleration"""
        logger.info(f"Initializing STT model: {self.hf_repo}")
        logger.info(f"Using device: {self.device}")
        
        try:
            # Download model files
            lm_config_path = hf_hub_download(self.hf_repo, "config.json")
            with open(lm_config_path, "r") as f:
                lm_config = json.load(f)
            
            # Download weights and tokenizer
            mimi_weights = hf_hub_download(self.hf_repo, lm_config["mimi_name"])
            moshi_weights = hf_hub_download(
                self.hf_repo, 
                lm_config.get("moshi_name", "model.safetensors")
            )
            tokenizer_path = hf_hub_download(
                self.hf_repo, 
                lm_config["tokenizer_name"]
            )
            
            # Initialize language model
            lm_config_obj = LmConfig.from_config_dict(lm_config)
            self.model = Lm(lm_config_obj)
            
            if self.device == "cuda":
                self.model = self.model.cuda()
                # Use bfloat16 for better GPU performance
                self.model = self.model.to(torch.bfloat16)
            
            self.model.load_state_dict(torch.load(moshi_weights, map_location=self.device))
            self.model.eval()
            
            # Initialize tokenizers
            self.text_tokenizer = sentencepiece.SentencePieceProcessor(tokenizer_path)
            
            # Initialize audio tokenizer (Mimi)
            generated_codebooks = lm_config_obj.generated_codebooks
            other_codebooks = lm_config_obj.other_codebooks
            mimi_codebooks = max(generated_codebooks, other_codebooks)
            
            if self.device == "cuda":
                # Use rustymimi for GPU acceleration
                self.audio_tokenizer = rustymimi.Tokenizer(
                    str(mimi_weights), 
                    num_codebooks=mimi_codebooks
                )
            else:
                # Fallback to Python implementation
                self.audio_tokenizer = mimi.Mimi(mimi.mimi_202407(32))
                self.audio_tokenizer.load_pytorch_weights(str(mimi_weights), strict=True)
            
            # Warmup model
            logger.info("Warming up model...")
            self.model.warmup() if hasattr(self.model, 'warmup') else None
            
            # Setup generation
            self.gen = utils.LmGen(
                model=self.model,
                max_steps=4096,
                text_sampler=utils.Sampler(top_k=25, temp=0),
                audio_sampler=utils.Sampler(top_k=250, temp=0.8),
                check=False,
            )
            
            logger.info(f"STT model initialized successfully on {self.device}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize STT model: {e}")
            return False
    
    def process_audio_chunk(self, audio_data: np.ndarray) -> str:
        """Process a chunk of audio data and return transcription"""
        try:
            # Ensure audio is in the right format (mono, correct sample rate)
            if len(audio_data.shape) > 1:
                audio_data = audio_data.mean(axis=1)  # Convert to mono
            
            # Pad audio to expected block size
            if len(audio_data) < self.block_size:
                padding = np.zeros(self.block_size - len(audio_data))
                audio_data = np.concatenate([audio_data, padding])
            elif len(audio_data) > self.block_size:
                audio_data = audio_data[:self.block_size]
            
            # Convert to tensor and move to device
            audio_tensor = torch.from_numpy(audio_data).float()
            if self.device == "cuda":
                audio_tensor = audio_tensor.cuda()
            
            # Add batch and channel dimensions
            audio_block = audio_tensor[None, None, :]  # [1, 1, block_size]
            
            with torch.no_grad():
                # Encode audio to tokens using Mimi
                if hasattr(self.audio_tokenizer, 'encode_step'):
                    # GPU path with rustymimi
                    other_audio_tokens = self.audio_tokenizer.encode_step(
                        audio_block[None, 0:1].cpu().numpy()
                    )
                    other_audio_tokens = torch.from_numpy(other_audio_tokens)
                    if self.device == "cuda":
                        other_audio_tokens = other_audio_tokens.cuda()
                    other_audio_tokens = other_audio_tokens.transpose(0, 2, 1)
                else:
                    # Fallback to Python Mimi
                    other_audio_tokens = self.audio_tokenizer.encode_step(audio_block)
                    other_audio_tokens = other_audio_tokens.transpose(0, 2, 1)
                
                # Generate text token
                text_token = self.gen.step(other_audio_tokens[0])
                text_token_id = text_token[0].item()
                
                # Decode text token
                if text_token_id not in (0, 3):  # Skip special tokens
                    text_piece = self.text_tokenizer.id_to_piece(text_token_id)
                    text_piece = text_piece.replace("▁", " ")
                    return text_piece
                
            return ""
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            return ""

# Global STT processor instance
stt_processor = STTProcessorGPU()

# FastAPI app
app = FastAPI(
    title="Kyutai STT CloudRun GPU Server",
    description="GPU-accelerated Speech-to-Text service using Kyutai STT models",
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
    return {
        "message": "Kyutai STT CloudRun GPU Server", 
        "status": "running",
        "device": stt_processor.device,
        "cuda_available": torch.cuda.is_available()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for CloudRun"""
    gpu_info = {}
    if torch.cuda.is_available():
        gpu_info = {
            "gpu_count": torch.cuda.device_count(),
            "gpu_name": torch.cuda.get_device_name(0),
            "gpu_memory_allocated": torch.cuda.memory_allocated(0),
            "gpu_memory_cached": torch.cuda.memory_reserved(0)
        }
    
    return {
        "status": "healthy",
        "model": stt_processor.hf_repo,
        "device": stt_processor.device,
        "timestamp": time.time(),
        **gpu_info
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
        start_time = time.time()
        transcription = stt_processor.process_audio_chunk(audio_np)
        processing_time = time.time() - start_time
        
        return {
            "transcription": transcription,
            "timestamp": time.time(),
            "audio_length": len(audio_np),
            "processing_time_ms": processing_time * 1000,
            "device": stt_processor.device
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
                        "processing_time_ms": processing_time * 1000,
                        "device": stt_processor.device
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
    
    logger.info(f"Starting GPU server on {host}:{port}")
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
        workers=1  # Single worker for CloudRun
    )