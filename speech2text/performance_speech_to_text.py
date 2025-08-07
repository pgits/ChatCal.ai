#!/usr/bin/env python3
"""
Performance-monitored Speech-to-Text using Moshi MLX
Based on delayed-streams-modeling for M3 MacBook optimization
"""

import argparse
import json
import queue
import time
import statistics
from collections import deque
from datetime import datetime

import mlx.core as mx
import mlx.nn as nn
import numpy as np
import rustymimi
import sentencepiece
import sounddevice as sd
from huggingface_hub import hf_hub_download
from moshi_mlx import models, utils


class PerformanceMonitor:
    def __init__(self, window_size=50):
        self.window_size = window_size
        self.audio_process_times = deque(maxlen=window_size)
        self.text_decode_times = deque(maxlen=window_size)
        self.total_process_times = deque(maxlen=window_size)
        self.word_count = 0
        self.start_time = time.time()
        
    def add_timing(self, audio_time, text_time, total_time):
        self.audio_process_times.append(audio_time * 1000)  # Convert to ms
        self.text_decode_times.append(text_time * 1000)
        self.total_process_times.append(total_time * 1000)
        
    def get_stats(self):
        if not self.total_process_times:
            return "No data yet"
            
        total_stats = {
            'avg': statistics.mean(self.total_process_times),
            'min': min(self.total_process_times),
            'max': max(self.total_process_times),
            'current': self.total_process_times[-1]
        }
        
        audio_stats = {
            'avg': statistics.mean(self.audio_process_times),
            'current': self.audio_process_times[-1]
        }
        
        text_stats = {
            'avg': statistics.mean(self.text_decode_times),
            'current': self.text_decode_times[-1]
        }
        
        return {
            'total_latency_ms': total_stats,
            'audio_processing_ms': audio_stats,
            'text_decoding_ms': text_stats,
            'words_transcribed': self.word_count,
            'runtime_seconds': time.time() - self.start_time
        }
    
    def print_live_stats(self):
        stats = self.get_stats()
        if stats == "No data yet":
            return
            
        print(f"\n--- PERFORMANCE STATS (last {len(self.total_process_times)} samples) ---")
        print(f"Current Latency: {stats['total_latency_ms']['current']:.1f}ms")
        print(f"Average Latency: {stats['total_latency_ms']['avg']:.1f}ms")
        print(f"Min/Max Latency: {stats['total_latency_ms']['min']:.1f}/{stats['total_latency_ms']['max']:.1f}ms")
        print(f"Words Transcribed: {stats['words_transcribed']}")
        print(f"Runtime: {stats['runtime_seconds']:.1f}s")
        print("---" * 20)


def main():
    parser = argparse.ArgumentParser(description="Performance-monitored Speech-to-Text with MLX")
    parser.add_argument("--max-steps", default=4096, type=int)
    parser.add_argument("--hf-repo", default="kyutai/stt-1b-en_fr-mlx", 
                       help="HuggingFace repository for the model")
    parser.add_argument("--vad", action="store_true", 
                       help="Enable VAD (Voice Activity Detection)")
    parser.add_argument("--stats-interval", default=10, type=int,
                       help="Print performance stats every N transcriptions")
    args = parser.parse_args()

    print("🎤 Setting up Performance-Monitored Speech-to-Text...")
    print(f"Model: {args.hf_repo}")
    print(f"VAD Enabled: {args.vad}")
    
    # Initialize performance monitor
    monitor = PerformanceMonitor()
    
    # Load model configuration
    print("\n📥 Downloading model files...")
    lm_config = hf_hub_download(args.hf_repo, "config.json")
    with open(lm_config, "r") as fobj:
        lm_config = json.load(fobj)
    
    mimi_weights = hf_hub_download(args.hf_repo, lm_config["mimi_name"])
    moshi_name = lm_config.get("moshi_name", "model.safetensors")
    moshi_weights = hf_hub_download(args.hf_repo, moshi_name)
    tokenizer = hf_hub_download(args.hf_repo, lm_config["tokenizer_name"])

    # Initialize model
    print("\n🧠 Initializing model...")
    lm_config = models.LmConfig.from_config_dict(lm_config)
    model = models.Lm(lm_config)
    model.set_dtype(mx.bfloat16)
    
    # Apply quantization if available
    if moshi_weights.endswith(".q4.safetensors"):
        print("  Applying 4-bit quantization...")
        nn.quantize(model, bits=4, group_size=32)
    elif moshi_weights.endswith(".q8.safetensors"):
        print("  Applying 8-bit quantization...")
        nn.quantize(model, bits=8, group_size=64)

    print(f"  Loading model weights from {moshi_weights}")
    model.load_weights(moshi_weights, strict=True)

    print(f"  Loading text tokenizer from {tokenizer}")
    text_tokenizer = sentencepiece.SentencePieceProcessor(tokenizer)

    print(f"  Loading audio tokenizer from {mimi_weights}")
    generated_codebooks = lm_config.generated_codebooks
    other_codebooks = lm_config.other_codebooks
    mimi_codebooks = max(generated_codebooks, other_codebooks)
    audio_tokenizer = rustymimi.Tokenizer(mimi_weights, num_codebooks=mimi_codebooks)
    
    print("🔥 Warming up model...")
    warmup_start = time.time()
    model.warmup()
    warmup_time = time.time() - warmup_start
    print(f"  Warmup completed in {warmup_time:.2f}s")
    
    # Initialize generation
    gen = models.LmGen(
        model=model,
        max_steps=args.max_steps,
        text_sampler=utils.Sampler(top_k=25, temp=0),
        audio_sampler=utils.Sampler(top_k=250, temp=0.8),
        check=False,
    )

    # Audio processing setup
    block_queue = queue.Queue()
    transcription_count = 0

    def audio_callback(indata, _frames, _time, _status):
        if _status:
            print(f"Audio callback status: {_status}")
        
        # Check audio level for debugging
        volume = np.linalg.norm(indata)
        if volume > 0.01:  # Only log when there's actual audio
            print(f".", end="", flush=True)  # Show activity indicator
            
        block_queue.put(indata.copy())

    print("\n🎙️  Recording audio from microphone...")
    print("Speak to see real-time transcription with performance metrics!")
    print("Press Ctrl+C to stop\n")
    
    last_print_was_vad = False
    
    # Check default sample rate and adjust if needed
    default_device = sd.query_devices(kind='input')
    default_samplerate = int(default_device['default_samplerate'])
    
    # Use 24kHz for the model, resample if needed
    model_samplerate = 24000
    if default_samplerate != model_samplerate:
        print(f"⚠️  Microphone default rate: {default_samplerate}Hz, model expects: {model_samplerate}Hz")
        print("   Resampling will be applied automatically by sounddevice")
    
    with sd.InputStream(
        channels=1,
        dtype="float32",
        samplerate=model_samplerate,  # Force 24kHz for model compatibility
        blocksize=1920,
        callback=audio_callback,
    ):
        try:
            while True:
                process_start = time.time()
                
                # Get audio block
                block = block_queue.get()
                block = block[None, :, 0]
                
                # Process audio tokens
                audio_start = time.time()
                other_audio_tokens = audio_tokenizer.encode_step(block[None, 0:1])
                other_audio_tokens = mx.array(other_audio_tokens).transpose(0, 2, 1)[
                    :, :, :other_codebooks
                ]
                audio_time = time.time() - audio_start
                
                # Generate text
                text_start = time.time()
                if args.vad:
                    text_token, vad_heads = gen.step_with_extra_heads(other_audio_tokens[0])
                    if vad_heads:
                        pr_vad = vad_heads[2][0, 0, 0].item()
                        if pr_vad > 0.5 and not last_print_was_vad:
                            print(" [🔇 end of turn detected]")
                            last_print_was_vad = True
                else:
                    text_token = gen.step(other_audio_tokens[0])
                
                text_token = text_token[0].item()
                audio_tokens = gen.last_audio_tokens()
                text_time = time.time() - text_start
                
                total_time = time.time() - process_start
                
                # Process text output
                if text_token not in (0, 3):
                    _text = text_tokenizer.id_to_piece(text_token)
                    _text = _text.replace("▁", " ")
                    print(_text, end="", flush=True)
                    monitor.word_count += len(_text.strip().split()) if _text.strip() else 0
                    last_print_was_vad = False
                
                # Record performance metrics
                monitor.add_timing(audio_time, text_time, total_time)
                transcription_count += 1
                
                # Print periodic stats
                if transcription_count % args.stats_interval == 0:
                    monitor.print_live_stats()
                    
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping transcription...")
            print("\n📊 FINAL PERFORMANCE REPORT:")
            final_stats = monitor.get_stats()
            if final_stats != "No data yet":
                print(f"Total Runtime: {final_stats['runtime_seconds']:.1f}s")
                print(f"Total Words Transcribed: {final_stats['words_transcribed']}")
                print(f"Average Latency: {final_stats['total_latency_ms']['avg']:.1f}ms")
                print(f"Best Latency: {final_stats['total_latency_ms']['min']:.1f}ms")
                print(f"Worst Latency: {final_stats['total_latency_ms']['max']:.1f}ms")
                print(f"Processing Rate: {transcription_count/final_stats['runtime_seconds']:.1f} tokens/sec")


if __name__ == "__main__":
    main()