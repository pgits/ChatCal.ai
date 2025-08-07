#!/usr/bin/env python3
"""
Buffered Speech-to-Text that accumulates audio for better transcription
"""

import argparse
import json
import queue
import time
import threading
from collections import deque

import mlx.core as mx
import mlx.nn as nn
import numpy as np
import rustymimi
import sentencepiece
import sounddevice as sd
from huggingface_hub import hf_hub_download
from moshi_mlx import models, utils


def main():
    parser = argparse.ArgumentParser(description="Buffered Speech-to-Text with MLX")
    parser.add_argument("--buffer-seconds", default=2.0, type=float,
                       help="Audio buffer duration in seconds")
    parser.add_argument("--hf-repo", default="kyutai/stt-1b-en_fr-mlx")
    args = parser.parse_args()

    print("🎤 Setting up Buffered Speech-to-Text...")
    print(f"Buffer duration: {args.buffer_seconds}s")
    
    # Load model
    print("📥 Loading model...")
    lm_config = hf_hub_download(args.hf_repo, "config.json")
    with open(lm_config, "r") as fobj:
        lm_config = json.load(fobj)
    
    mimi_weights = hf_hub_download(args.hf_repo, lm_config["mimi_name"])
    moshi_weights = hf_hub_download(args.hf_repo, lm_config.get("moshi_name", "model.safetensors"))
    tokenizer = hf_hub_download(args.hf_repo, lm_config["tokenizer_name"])

    lm_config = models.LmConfig.from_config_dict(lm_config)
    model = models.Lm(lm_config)
    model.set_dtype(mx.bfloat16)
    model.load_weights(moshi_weights, strict=True)

    text_tokenizer = sentencepiece.SentencePieceProcessor(tokenizer)
    
    # Use the same audio tokenizer setup as the working file example
    audio_tokenizer = models.mimi.Mimi(models.mimi_202407(32))
    audio_tokenizer.load_pytorch_weights(str(mimi_weights), strict=True)
    
    print("🔥 Warming up model...")
    model.warmup()
    gen = models.LmGen(
        model=model,
        max_steps=4096,
        text_sampler=utils.Sampler(top_k=25, temp=0),
        audio_sampler=utils.Sampler(top_k=250, temp=0.8),
        check=False,
    )

    # Audio recording setup
    samplerate = 24000
    buffer_size = int(args.buffer_seconds * samplerate)
    audio_buffer = np.zeros((buffer_size,), dtype=np.float32)
    buffer_pos = 0
    audio_lock = threading.Lock()
    
    def audio_callback(indata, frames, time, status):
        nonlocal buffer_pos
        if status:
            print(f"Audio status: {status}")
        
        with audio_lock:
            # Add new audio to circular buffer
            audio_data = indata[:, 0]  # Take first channel
            end_pos = buffer_pos + len(audio_data)
            
            if end_pos <= buffer_size:
                audio_buffer[buffer_pos:end_pos] = audio_data
            else:
                # Wrap around
                first_part = buffer_size - buffer_pos
                audio_buffer[buffer_pos:] = audio_data[:first_part]
                audio_buffer[:end_pos-buffer_size] = audio_data[first_part:]
            
            buffer_pos = end_pos % buffer_size
    
    def process_audio_buffer():
        """Process accumulated audio buffer"""
        with audio_lock:
            # Get current buffer content (in correct order)
            if buffer_pos == 0:
                current_audio = audio_buffer.copy()
            else:
                current_audio = np.concatenate([
                    audio_buffer[buffer_pos:],
                    audio_buffer[:buffer_pos]
                ])
        
        # Convert to MLX format
        audio = mx.array(current_audio[None, :])  # Add batch dimension
        
        # Add padding for processing
        audio = mx.concat([audio, mx.zeros((1, 48000))], axis=-1)
        
        print("🔄 Processing buffer...", end=" ", flush=True)
        transcription_parts = []
        
        # Process in chunks (same as working file example)
        for start_idx in range(0, audio.shape[-1] // 1920 * 1920, 1920):
            block = audio[:, None, start_idx:start_idx + 1920]
            other_audio_tokens = audio_tokenizer.encode_step(block).transpose(0, 2, 1)
            
            text_token = gen.step(other_audio_tokens[0])
            text_token = text_token[0].item()
            
            if text_token not in (0, 3):
                _text = text_tokenizer.id_to_piece(text_token)
                _text = _text.replace("▁", " ")
                transcription_parts.append(_text)
        
        transcription = "".join(transcription_parts).strip()
        if transcription:
            print(f"✅ '{transcription}'")
        else:
            print("❌ No speech detected")
        
        return transcription

    print(f"\n🎙️  Recording audio in {args.buffer_seconds}s buffers...")
    print("Speak for a few seconds, then pause. Press Ctrl+C to stop\n")
    
    with sd.InputStream(
        callback=audio_callback,
        channels=1,
        samplerate=samplerate,
        blocksize=1920,
        dtype='float32'
    ):
        try:
            while True:
                time.sleep(args.buffer_seconds)  # Wait for buffer to fill
                process_audio_buffer()
                time.sleep(0.1)  # Brief pause
                
        except KeyboardInterrupt:
            print("\n🛑 Stopped recording")

if __name__ == "__main__":
    main()