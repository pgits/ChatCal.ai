#!/usr/bin/env python3
"""
Simple test to verify transcription is working
"""

import json
import time
import mlx.core as mx
import numpy as np
import rustymimi
import sentencepiece
import sounddevice as sd
from huggingface_hub import hf_hub_download
from moshi_mlx import models, utils

def main():
    print("🧪 Simple Speech-to-Text Test")
    
    # Load model (using cached files)
    hf_repo = "kyutai/stt-1b-en_fr-mlx"
    lm_config = hf_hub_download(hf_repo, "config.json")
    with open(lm_config, "r") as fobj:
        lm_config = json.load(fobj)
    
    mimi_weights = hf_hub_download(hf_repo, lm_config["mimi_name"])
    moshi_weights = hf_hub_download(hf_repo, lm_config.get("moshi_name", "model.safetensors"))
    tokenizer = hf_hub_download(hf_repo, lm_config["tokenizer_name"])

    # Initialize model
    lm_config = models.LmConfig.from_config_dict(lm_config)
    model = models.Lm(lm_config)
    model.set_dtype(mx.bfloat16)
    model.load_weights(moshi_weights, strict=True)

    text_tokenizer = sentencepiece.SentencePieceProcessor(tokenizer)
    
    generated_codebooks = lm_config.generated_codebooks
    other_codebooks = lm_config.other_codebooks
    mimi_codebooks = max(generated_codebooks, other_codebooks)
    audio_tokenizer = rustymimi.Tokenizer(mimi_weights, num_codebooks=mimi_codebooks)
    
    model.warmup()
    gen = models.LmGen(
        model=model,
        max_steps=4096,
        text_sampler=utils.Sampler(top_k=25, temp=0),
        audio_sampler=utils.Sampler(top_k=250, temp=0.8),
        check=False,
    )
    
    print("🎤 Recording 5 seconds of audio. Speak clearly...")
    
    # Record audio
    duration = 5
    samplerate = 24000
    recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='float32')
    
    for i in range(duration):
        print(f"Recording... {i+1}/{duration}")
        time.sleep(1)
    
    sd.wait()  # Wait until recording is finished
    print("✅ Recording complete. Processing...")
    
    # Process the recording
    audio = mx.array(recording.T)  # Transpose to match expected shape
    
    # Add padding and process in chunks
    audio = mx.concat([audio, mx.zeros((1, 48000))], axis=-1)
    
    transcription_parts = []
    print("🔄 Transcribing...")
    
    for start_idx in range(0, audio.shape[-1] // 1920 * 1920, 1920):
        block = audio[:, None, start_idx:start_idx + 1920]
        other_audio_tokens = audio_tokenizer.encode_step(block[None, 0:1])
        other_audio_tokens = mx.array(other_audio_tokens).transpose(0, 2, 1)[:, :, :other_codebooks]
        
        text_token = gen.step(other_audio_tokens[0])
        text_token = text_token[0].item()
        
        if text_token not in (0, 3):
            _text = text_tokenizer.id_to_piece(text_token)
            _text = _text.replace("▁", " ")
            transcription_parts.append(_text)
            print(_text, end="", flush=True)
    
    print("\n")
    final_transcription = "".join(transcription_parts)
    
    if final_transcription.strip():
        print(f"✅ Transcription: '{final_transcription.strip()}'")
    else:
        print("❌ No transcription generated - try speaking louder or closer to microphone")

if __name__ == "__main__":
    main()