from transformers import AutoTokenizer

# Test if you can access the model
try:
    tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
    print("✅ Qwen2.5-7B-Instruct - Access granted!")
except Exception as e:
    print(f"❌ Error: {e}")

try:
    tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-3-mini-128k-instruct")
    print("✅ Phi-3-mini - Access granted!")
except Exception as e:
    print(f"❌ Error: {e}")
