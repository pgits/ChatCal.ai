#!/usr/bin/env python3
"""
Low-latency Speech-to-Text with variable buffer sizes for testing latency vs accuracy
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
    parser = argparse.ArgumentParser(description="Low-latency Speech-to-Text Testing")
    parser.add_argument("--buffer-ms", default=500, type=int,
                       help="Audio buffer duration in milliseconds (100-3000)")
    parser.add_argument("--overlap-ms", default=100, type=int,
                       help="Overlap between buffers in milliseconds")
    parser.add_argument("--hf-repo", default="kyutai/stt-1b-en_fr-mlx")
    parser.add_argument("--show-timing", action="store_true",
                       help="Show detailed timing information")
    args = parser.parse_args()

    buffer_seconds = args.buffer_ms / 1000.0
    overlap_seconds = args.overlap_ms / 1000.0

    print("⚡ Low-Latency Speech-to-Text")
    print(f"Buffer: {args.buffer_ms}ms ({buffer_seconds}s)")
    print(f"Overlap: {args.overlap_ms}ms")
    print(f"Expected total delay: ~{args.buffer_ms + 100}ms")
    
    # Load model (using cached files for speed)
    print("\n📥 Loading cached model...")
    load_start = time.time()
    
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
    audio_tokenizer = models.mimi.Mimi(models.mimi_202407(32))
    audio_tokenizer.load_pytorch_weights(str(mimi_weights), strict=True)
    
    model.warmup()
    gen = models.LmGen(
        model=model,
        max_steps=4096,
        text_sampler=utils.Sampler(top_k=25, temp=0),
        audio_sampler=utils.Sampler(top_k=250, temp=0.8),
        check=False,
    )
    
    load_time = time.time() - load_start
    print(f"✅ Model loaded in {load_time:.2f}s")

    # Audio setup with smaller buffers
    samplerate = 24000
    buffer_samples = int(buffer_seconds * samplerate)
    overlap_samples = int(overlap_seconds * samplerate)
    
    # Rolling buffer for continuous processing
    audio_buffer = np.zeros((buffer_samples + overlap_samples,), dtype=np.float32)
    buffer_pos = 0
    audio_lock = threading.Lock()
    last_process_time = time.time()
    
    # Statistics
    process_times = deque(maxlen=20)
    transcription_count = 0
    
    def audio_callback(indata, frames, time, status):
        nonlocal buffer_pos
        if status and args.show_timing:
            print(f"Audio callback status: {status}")
        
        with audio_lock:
            audio_data = indata[:, 0]
            
            # Add to rolling buffer
            for sample in audio_data:
                audio_buffer[buffer_pos] = sample
                buffer_pos = (buffer_pos + 1) % len(audio_buffer)
    
    def process_audio_buffer():
        """Process current audio buffer with timing"""
        nonlocal transcription_count
        
        process_start = time.time()
        
        with audio_lock:
            # Get current buffer state
            if buffer_pos < buffer_samples:
                # Not enough data yet
                return None
            
            # Extract buffer with overlap
            current_audio = np.zeros(buffer_samples, dtype=np.float32)
            start_idx = (buffer_pos - buffer_samples) % len(audio_buffer)
            
            if start_idx + buffer_samples <= len(audio_buffer):
                current_audio = audio_buffer[start_idx:start_idx + buffer_samples].copy()
            else:
                # Wrap around
                first_part = len(audio_buffer) - start_idx
                current_audio[:first_part] = audio_buffer[start_idx:]
                current_audio[first_part:] = audio_buffer[:buffer_samples - first_part]
        
        # Check if there's actual audio content
        audio_level = np.max(np.abs(current_audio))
        if audio_level < 0.001:
            return None  # Too quiet, skip processing
        
        # Convert to MLX and process
        audio = mx.array(current_audio[None, :])
        audio = mx.concat([audio, mx.zeros((1, 48000))], axis=-1)
        
        transcription_parts = []
        chunk_start = time.time()
        
        # Process in chunks
        for start_idx in range(0, audio.shape[-1] // 1920 * 1920, 1920):
            block = audio[:, None, start_idx:start_idx + 1920]
            other_audio_tokens = audio_tokenizer.encode_step(block).transpose(0, 2, 1)
            
            text_token = gen.step(other_audio_tokens[0])
            text_token = text_token[0].item()
            
            if text_token not in (0, 3):
                _text = text_tokenizer.id_to_piece(text_token)
                _text = _text.replace("▁", " ")
                transcription_parts.append(_text)
        
        chunk_time = time.time() - chunk_start
        total_time = time.time() - process_start
        
        process_times.append(total_time * 1000)  # Convert to ms
        transcription = "".join(transcription_parts).strip()
        
        if transcription:
            transcription_count += 1
            avg_latency = sum(process_times) / len(process_times) if process_times else 0
            
            if args.show_timing:
                print(f"[{total_time*1000:.1f}ms] '{transcription}' (avg: {avg_latency:.1f}ms)")
            else:
                print(f"✅ '{transcription}'")
            
            return transcription
        elif args.show_timing:
            print(f"[{total_time*1000:.1f}ms] ❌ No speech (level: {audio_level:.4f})")
        
        return None

    print(f"\n🎙️  Recording with {args.buffer_ms}ms buffers...")
    print("Speak naturally. Press Ctrl+C to stop\n")
    
    with sd.InputStream(
        callback=audio_callback,
        channels=1,
        samplerate=samplerate,
        blocksize=int(samplerate * 0.08),  # ~80ms blocks
        dtype='float32'
    ):
        try:
            while True:
                time.sleep(buffer_seconds)  # Wait for buffer to fill
                process_audio_buffer()
                
        except KeyboardInterrupt:
            print(f"\n🛑 Stopped recording")
            
            if process_times:
                avg_latency = sum(process_times) / len(process_times)
                min_latency = min(process_times)
                max_latency = max(process_times)
                
                print(f"\n📊 Performance Summary:")
                print(f"   Transcriptions: {transcription_count}")
                print(f"   Average processing: {avg_latency:.1f}ms")
                print(f"   Min/Max processing: {min_latency:.1f}/{max_latency:.1f}ms") 
                print(f"   Total end-to-end delay: ~{args.buffer_ms + avg_latency:.0f}ms")
            else:
                print("No transcriptions processed")

if __name__ == "__main__":
    main()