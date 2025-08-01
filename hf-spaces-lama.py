# Simple integration - no local models needed!
from llama_index.llms.huggingface_api import HuggingFaceInferenceAPI

# Try different models that are available via HF Inference API
models_to_try = [
    "microsoft/DialoGPT-medium",
    "microsoft/DialoGPT-large", 
    "HuggingFaceH4/zephyr-7b-beta",
    "mistralai/Mistral-7B-Instruct-v0.1",
    "meta-llama/Llama-2-7b-chat-hf"
]

print("Testing Hugging Face Inference API with different models...")

for model_name in models_to_try:
    print(f"\nTrying model: {model_name}")
    try:
        llm = HuggingFaceInferenceAPI(
            model_name=model_name,
            # token="your_hf_token"  # Optional for higher rate limits
        )
        
        response = llm.complete("Hello, how are you?")
        print(f"✅ Success with {model_name}")
        print(f"Response: {response.text}")
        break
        
    except Exception as e:
        print(f"❌ Failed with {model_name}: {str(e)[:100]}...")
        continue
        
print("\nNote: Some models may require a Hugging Face token or may not be available via the inference API.")
