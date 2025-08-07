#!/usr/bin/env python3
"""
Download Kyutai STT models for pre-caching in Docker container
"""

import os
import glob
from huggingface_hub import hf_hub_download

# Set cache directory
os.environ['HF_HOME'] = '/app/models'
os.environ['TRANSFORMERS_CACHE'] = '/app/models'
os.environ['HF_DATASETS_CACHE'] = '/app/models'

print('Downloading Kyutai STT model files...')

# Download main model files
try:
    repo_id = 'kyutai/stt-1b-en_fr'  # Use the STT-specific model with proper structure
    
    print(f'📥 Downloading from {repo_id}...')
    
    # Download config file
    config_file = hf_hub_download(repo_id, 'config.json', cache_dir='/app/models')
    print(f'✅ Downloaded config: {config_file}')
    
    # Download main STT model (largest file ~1.98GB)
    print('📥 Downloading main STT model file (~2GB)...')
    model_file = hf_hub_download(repo_id, 'model.safetensors', cache_dir='/app/models')
    print(f'✅ Downloaded model: {model_file}')
    
    # Download mimi encoder (385MB) - essential for audio tokenization
    print('📥 Downloading mimi encoder (385MB)...')
    mimi_file = hf_hub_download(repo_id, 'mimi-pytorch-e351c8d8@125.safetensors', cache_dir='/app/models')
    print(f'✅ Downloaded mimi: {mimi_file}')
    
    # Download tokenizer
    tokenizer_file = hf_hub_download(repo_id, 'tokenizer_en_fr_audio_8000.model', cache_dir='/app/models')
    print(f'✅ Downloaded tokenizer: {tokenizer_file}')
    
    print('🎉 All model files cached successfully!')
    
    # Verify files exist and print sizes
    print('\n📊 Model cache summary:')
    model_files = glob.glob('/app/models/**/*', recursive=True)
    total_size = 0
    
    for f in sorted(model_files):
        if os.path.isfile(f):
            size = os.path.getsize(f)
            total_size += size
            size_mb = size / 1024 / 1024
            if size_mb > 10:  # Only show files larger than 10MB
                print(f'  📄 {os.path.basename(f)}: {size_mb:.1f} MB')
    
    total_gb = total_size / 1024 / 1024 / 1024
    print(f'\n💾 Total cached model size: {total_gb:.2f} GB')
    print(f'📁 Cache location: /app/models')
    
except Exception as e:
    print(f'❌ Failed to pre-download models: {e}')
    print('⚠️  Models will be downloaded at runtime instead')
    raise  # Re-raise to fail the build if models can't be downloaded