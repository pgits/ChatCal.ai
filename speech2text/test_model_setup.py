#!/usr/bin/env python3
"""
Test script to validate model setup and download
"""

import json
import time
from huggingface_hub import hf_hub_download
from moshi_mlx import models

def test_model_download():
    print("🧪 Testing model download and initialization...")
    
    # Test with smaller 1B model first
    hf_repo = "kyutai/stt-1b-en_fr-mlx"
    
    print(f"📥 Downloading config from {hf_repo}")
    lm_config = hf_hub_download(hf_repo, "config.json")
    
    with open(lm_config, "r") as fobj:
        config_data = json.load(fobj)
    
    print("✅ Config downloaded successfully")
    print(f"Model details: {config_data.get('model_type', 'Unknown')} - {config_data.get('vocab_size', 'Unknown')} vocab")
    
    # Download other required files
    print("📥 Downloading model files...")
    mimi_weights = hf_hub_download(hf_repo, config_data["mimi_name"])
    moshi_weights = hf_hub_download(hf_repo, config_data.get("moshi_name", "model.safetensors"))
    tokenizer = hf_hub_download(hf_repo, config_data["tokenizer_name"])
    
    print("✅ All model files downloaded successfully")
    print(f"  Audio tokenizer: {mimi_weights}")
    print(f"  Language model: {moshi_weights}")
    print(f"  Text tokenizer: {tokenizer}")
    
    # Test model initialization
    print("🧠 Testing model initialization...")
    start_time = time.time()
    
    lm_config = models.LmConfig.from_config_dict(config_data)
    model = models.Lm(lm_config)
    
    init_time = time.time() - start_time
    print(f"✅ Model initialized in {init_time:.2f}s")
    
    # Test model loading
    print("📂 Testing model weight loading...")
    start_time = time.time()
    
    model.load_weights(moshi_weights, strict=True)
    
    load_time = time.time() - start_time
    print(f"✅ Model weights loaded in {load_time:.2f}s")
    
    print("\n🎉 Model setup test completed successfully!")
    print("Ready to run real-time speech recognition.")

if __name__ == "__main__":
    test_model_download()