#!/usr/bin/env python3
"""
Final latency test using exactly the same code as working buffered version
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

def test_latency(buffer_seconds):
    print(f"⚡ Testing {buffer_seconds}s buffer latency")
    
    # Load model (exact same as buffered version)
    hf_repo = "kyutai/stt-1b-en_fr-mlx"
    lm_config = hf_hub_download(hf_repo, "config.json")
    with open(lm_config, "r") as fobj:
        lm_config = json.load(fobj)
    
    mimi_weights = hf_hub_download(hf_repo, lm_config["mimi_name"])
    moshi_weights = hf_hub_download(hf_repo, lm_config.get("moshi_name", "model.safetensors"))
    tokenizer = hf_hub_download(hf_repo, lm_config["tokenizer_name"])

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

    # Audio setup (exact same as buffered version)
    samplerate = 24000
    buffer_size = int(buffer_seconds * samplerate)
    audio_buffer = np.zeros((buffer_size,), dtype=np.float32)
    buffer_pos = 0
    audio_lock = threading.Lock()
    
    def audio_callback(indata, frames, time, status):
        nonlocal buffer_pos
        with audio_lock:
            audio_data = indata[:, 0]
            end_pos = buffer_pos + len(audio_data)
            
            if end_pos <= buffer_size:
                audio_buffer[buffer_pos:end_pos] = audio_data
            else:
                first_part = buffer_size - buffer_pos
                audio_buffer[buffer_pos:] = audio_data[:first_part]
                audio_buffer[:end_pos-buffer_size] = audio_data[first_part:]
            
            buffer_pos = end_pos % buffer_size
    
    def process_with_timing():
        """Process buffer with precise timing measurement"""
        with audio_lock:
            if buffer_pos == 0:
                current_audio = audio_buffer.copy()
            else:
                current_audio = np.concatenate([
                    audio_buffer[buffer_pos:],
                    audio_buffer[:buffer_pos]
                ])
        
        # Check audio level
        audio_level = np.max(np.abs(current_audio))
        if audio_level < 0.005:  # Lower threshold
            return None, 0, audio_level
        
        # Time the processing (exact same as buffered version)
        process_start = time.time()
        
        audio = mx.array(current_audio[None, :])
        audio = mx.concat([audio, mx.zeros((1, 48000))], axis=-1)
        
        transcription_parts = []
        
        for start_idx in range(0, audio.shape[-1] // 1920 * 1920, 1920):
            block = audio[:, None, start_idx:start_idx + 1920]
            other_audio_tokens = audio_tokenizer.encode_step(block).transpose(0, 2, 1)
            
            text_token = gen.step(other_audio_tokens[0])
            text_token = text_token[0].item()
            
            if text_token not in (0, 3):
                _text = text_tokenizer.id_to_piece(text_token)
                _text = _text.replace("▁", " ")
                transcription_parts.append(_text)
        
        processing_time = (time.time() - process_start) * 1000
        transcription = "".join(transcription_parts).strip()
        
        return transcription, processing_time, audio_level

    print(f"🎤 Speak for {buffer_seconds} seconds, then I'll measure processing time")
    print("The total user-experienced delay = buffer time + processing time")
    print("Press Ctrl+C after a few tests\n")
    
    test_count = 0
    processing_times = []
    
    with sd.InputStream(
        callback=audio_callback,
        channels=1,
        samplerate=samplerate,
        blocksize=1920,
        dtype='float32'
    ):
        try:
            while True:
                time.sleep(buffer_seconds)  # Wait for buffer
                
                transcription, proc_time, audio_level = process_with_timing()
                total_delay = buffer_seconds * 1000 + proc_time
                
                if transcription:
                    test_count += 1
                    processing_times.append(proc_time)
                    
                    print(f"✅ Test #{test_count}: '{transcription}'")
                    print(f"   Buffer time: {buffer_seconds*1000:.0f}ms")
                    print(f"   Processing time: {proc_time:.1f}ms") 
                    print(f"   Total user delay: {total_delay:.1f}ms")
                    print(f"   Audio level: {audio_level:.4f}\n")
                    
                else:
                    print(f"❌ No transcription (audio level: {audio_level:.4f})")
                
        except KeyboardInterrupt:
            print(f"\n🛑 Test completed")
            
            if processing_times:
                avg_processing = sum(processing_times) / len(processing_times)
                avg_total = buffer_seconds * 1000 + avg_processing
                
                print(f"\n📊 Results Summary ({test_count} successful tests):")
                print(f"   Buffer duration: {buffer_seconds*1000:.0f}ms")
                print(f"   Average processing: {avg_processing:.1f}ms")
                print(f"   Average total delay: {avg_total:.1f}ms")
                print(f"   Range: {min(processing_times):.1f} - {max(processing_times):.1f}ms processing")

if __name__ == "__main__":
    import sys
    buffer_seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    test_latency(buffer_seconds)