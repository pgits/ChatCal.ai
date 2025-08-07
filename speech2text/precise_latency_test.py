#!/usr/bin/env python3
"""
Precise end-to-end latency measurement from when you stop speaking to when text appears
"""

import json
import time
import threading
import numpy as np
import sounddevice as sd
import mlx.core as mx
from huggingface_hub import hf_hub_download
from moshi_mlx import models, utils
import sentencepiece

class LatencyTester:
    def __init__(self, buffer_seconds=1.0):
        self.buffer_seconds = buffer_seconds
        self.samplerate = 24000
        self.buffer_samples = int(buffer_seconds * self.samplerate)
        
        # Audio tracking
        self.audio_buffer = np.zeros((self.buffer_samples,), dtype=np.float32)
        self.buffer_pos = 0
        self.audio_lock = threading.Lock()
        
        # Timing tracking
        self.last_speech_time = None
        self.silence_threshold = 0.01  # Threshold to detect end of speech
        self.silence_duration = 0.3   # How long silence before considering speech ended
        
        self.load_model()
    
    def load_model(self):
        """Load the speech recognition model"""
        print("📥 Loading model...")
        hf_repo = "kyutai/stt-1b-en_fr-mlx"
        
        lm_config = hf_hub_download(hf_repo, "config.json")
        with open(lm_config, "r") as fobj:
            lm_config = json.load(fobj)
        
        mimi_weights = hf_hub_download(hf_repo, lm_config["mimi_name"])
        moshi_weights = hf_hub_download(hf_repo, lm_config.get("moshi_name", "model.safetensors"))
        tokenizer = hf_hub_download(hf_repo, lm_config["tokenizer_name"])

        lm_config = models.LmConfig.from_config_dict(lm_config)
        self.model = models.Lm(lm_config)
        self.model.set_dtype(mx.bfloat16)
        self.model.load_weights(moshi_weights, strict=True)

        self.text_tokenizer = sentencepiece.SentencePieceProcessor(tokenizer)
        self.audio_tokenizer = models.mimi.Mimi(models.mimi_202407(32))
        self.audio_tokenizer.load_pytorch_weights(str(mimi_weights), strict=True)
        
        self.model.warmup()
        self.gen = models.LmGen(
            model=self.model,
            max_steps=4096,
            text_sampler=utils.Sampler(top_k=25, temp=0),
            audio_sampler=utils.Sampler(top_k=250, temp=0.8),
            check=False,
        )
        print("✅ Model loaded")
    
    def audio_callback(self, indata, frames, cb_time, status):
        """Audio callback that tracks speech activity"""
        if status:
            print(f"Audio status: {status}")
        
        with self.audio_lock:
            audio_data = indata[:, 0]
            
            # Check current audio level
            current_level = np.max(np.abs(audio_data))
            
            # Update speech timing
            if current_level > self.silence_threshold:
                self.last_speech_time = time.time()
            
            # Add to rolling buffer
            for sample in audio_data:
                self.audio_buffer[self.buffer_pos] = sample
                self.buffer_pos = (self.buffer_pos + 1) % len(self.audio_buffer)
    
    def is_speech_ended(self):
        """Check if speech has ended (silence for specified duration)"""
        if self.last_speech_time is None:
            return False
        
        return (time.time() - self.last_speech_time) > self.silence_duration
    
    def process_current_buffer(self):
        """Process the current audio buffer and return transcription"""
        with self.audio_lock:
            # Get current buffer content
            current_audio = np.zeros(self.buffer_samples, dtype=np.float32)
            start_idx = (self.buffer_pos - self.buffer_samples) % len(self.audio_buffer)
            
            if start_idx + self.buffer_samples <= len(self.audio_buffer):
                current_audio = self.audio_buffer[start_idx:start_idx + self.buffer_samples].copy()
            else:
                # Wrap around
                first_part = len(self.audio_buffer) - start_idx
                current_audio[:first_part] = self.audio_buffer[start_idx:]
                current_audio[first_part:] = self.audio_buffer[:self.buffer_samples - first_part]
        
        # Check if there's meaningful audio
        audio_level = np.max(np.abs(current_audio))
        if audio_level < 0.001:
            return None, audio_level
        
        # Process the audio
        audio = mx.array(current_audio[None, :])
        audio = mx.concat([audio, mx.zeros((1, 48000))], axis=-1)
        
        transcription_parts = []
        
        # Process in chunks
        for start_idx in range(0, audio.shape[-1] // 1920 * 1920, 1920):
            block = audio[:, None, start_idx:start_idx + 1920]
            other_audio_tokens = self.audio_tokenizer.encode_step(block).transpose(0, 2, 1)
            
            text_token = self.gen.step(other_audio_tokens[0])
            text_token = text_token[0].item()
            
            if text_token not in (0, 3):
                _text = self.text_tokenizer.id_to_piece(text_token)
                _text = _text.replace("▁", " ")
                transcription_parts.append(_text)
        
        transcription = "".join(transcription_parts).strip()
        return transcription, audio_level
    
    def run_test(self):
        """Run the precise latency test"""
        print(f"\n🎯 Precise Latency Test ({self.buffer_seconds}s buffer)")
        print("Instructions:")
        print("1. Speak a short phrase")
        print("2. Stop talking and stay quiet")
        print("3. I'll measure from when you stop to when text appears")
        print("\nPress Ctrl+C to stop\n")
        
        test_count = 0
        total_latencies = []
        
        with sd.InputStream(
            callback=self.audio_callback,
            channels=1,
            samplerate=self.samplerate,
            blocksize=int(self.samplerate * 0.08),
            dtype='float32'
        ):
            try:
                while True:
                    time.sleep(0.1)  # Check every 100ms
                    
                    # Check if speech just ended
                    if self.is_speech_ended() and self.last_speech_time:
                        # Speech ended, start timing
                        speech_end_time = self.last_speech_time + self.silence_duration
                        
                        print("🔄 Speech ended, processing...", end=" ", flush=True)
                        
                        process_start = time.time()
                        transcription, audio_level = self.process_current_buffer()
                        process_end = time.time()
                        
                        # Calculate true end-to-end latency
                        true_latency = process_end - speech_end_time
                        processing_time = process_end - process_start
                        
                        if transcription:
                            test_count += 1
                            total_latencies.append(true_latency * 1000)  # Convert to ms
                            
                            print(f"\n✅ Test #{test_count}: '{transcription}'")
                            print(f"   End-to-end latency: {true_latency*1000:.1f}ms")
                            print(f"   Processing time: {processing_time*1000:.1f}ms")
                            print(f"   Audio level: {audio_level:.4f}")
                            
                            if test_count >= 3:
                                avg_latency = sum(total_latencies) / len(total_latencies)
                                print(f"\n📊 Average latency after {test_count} tests: {avg_latency:.1f}ms")
                        else:
                            print(f"❌ No transcription (level: {audio_level:.4f})")
                        
                        # Reset speech tracking
                        self.last_speech_time = None
                        time.sleep(1)  # Brief pause between tests
                        
            except KeyboardInterrupt:
                print(f"\n🛑 Testing stopped")
                
                if total_latencies:
                    avg_latency = sum(total_latencies) / len(total_latencies)
                    min_latency = min(total_latencies)
                    max_latency = max(total_latencies)
                    
                    print(f"\n📊 Final Results ({test_count} successful tests):")
                    print(f"   Average latency: {avg_latency:.1f}ms")
                    print(f"   Min latency: {min_latency:.1f}ms") 
                    print(f"   Max latency: {max_latency:.1f}ms")
                    print(f"   Buffer size: {self.buffer_seconds*1000:.0f}ms")
                else:
                    print("No successful transcriptions recorded")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--buffer-seconds", default=1.0, type=float,
                       help="Buffer size in seconds")
    args = parser.parse_args()
    
    tester = LatencyTester(args.buffer_seconds)
    tester.run_test()