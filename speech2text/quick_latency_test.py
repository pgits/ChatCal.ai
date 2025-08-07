#!/usr/bin/env python3
"""
Quick latency test with different buffer sizes
"""

import argparse
import json
import time
import numpy as np
import sounddevice as sd
import mlx.core as mx
from huggingface_hub import hf_hub_download
from moshi_mlx import models, utils
import sentencepiece

def test_buffer_size(buffer_ms, model_components):
    """Test a specific buffer size"""
    model, text_tokenizer, audio_tokenizer, gen = model_components
    
    print(f"\n🧪 Testing {buffer_ms}ms buffer...")
    
    samplerate = 24000
    buffer_samples = int((buffer_ms / 1000.0) * samplerate)
    
    print(f"Recording {buffer_ms}ms of audio...")
    recording = sd.rec(buffer_samples, samplerate=samplerate, channels=1, dtype='float32')
    
    # Show countdown
    for i in range(int(buffer_ms / 100)):
        time.sleep(0.1)
        print(".", end="", flush=True)
    
    sd.wait()
    print(" Done!")
    
    # Check if we got actual audio
    audio_level = np.max(np.abs(recording))
    print(f"   Audio level: {audio_level:.4f}")
    
    if audio_level < 0.001:
        return False, buffer_ms, "Audio too quiet"
    
    # Process the recording (same format as working buffered version)
    process_start = time.time()
    
    audio = mx.array(recording[:, 0][None, :])  # Take first channel, add batch dimension
    audio = mx.concat([audio, mx.zeros((1, 48000))], axis=-1)  # Add padding
    
    transcription_parts = []
    
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
    
    process_time = (time.time() - process_start) * 1000
    transcription = "".join(transcription_parts).strip()
    total_delay = buffer_ms + process_time
    
    print(f"   Processing time: {process_time:.1f}ms")
    print(f"   Total delay: {total_delay:.1f}ms")
    
    if transcription:
        print(f"   Result: ✅ '{transcription}'")
        return True, total_delay, transcription
    else:
        print(f"   Result: ❌ No transcription")
        return False, total_delay, ""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-sizes", default="300,500,800,1000", 
                       help="Comma-separated buffer sizes in ms")
    args = parser.parse_args()
    
    buffer_sizes = [int(x) for x in args.test_sizes.split(",")]
    
    print("⚡ Latency vs Accuracy Test")
    print(f"Testing buffer sizes: {buffer_sizes}ms")
    
    # Load model once
    print("\n📥 Loading model...")
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
    
    model_components = (model, text_tokenizer, audio_tokenizer, gen)
    
    # Test each buffer size
    results = []
    
    for buffer_ms in buffer_sizes:
        try:
            success, delay, transcription = test_buffer_size(buffer_ms, model_components)
            results.append((buffer_ms, success, delay, transcription))
            time.sleep(1)  # Brief pause between tests
        except KeyboardInterrupt:
            print("\n⏹️  Testing stopped by user")
            break
    
    # Summary
    print("\n📊 Results Summary:")
    print("Buffer(ms) | Success | Total Delay | Transcription")
    print("-" * 60)
    
    for buffer_ms, success, delay, transcription in results:
        status = "✅" if success else "❌"
        transcription_preview = transcription[:30] + "..." if len(transcription) > 30 else transcription
        print(f"{buffer_ms:9} | {status:7} | {delay:8.1f}ms | {transcription_preview}")
    
    # Find best performing size
    successful_results = [(delay, buffer_ms, trans) for buffer_ms, success, delay, trans in results if success]
    if successful_results:
        best_delay, best_buffer, best_trans = min(successful_results)
        print(f"\n🎯 Best performance: {best_buffer}ms buffer = {best_delay:.1f}ms total delay")

if __name__ == "__main__":
    main()