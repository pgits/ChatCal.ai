from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.chat_engine import SimpleChatEngine
import torch
import nltk
import ssl

# Fix SSL certificate issues for NLTK downloads
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Download required NLTK data
try:
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
except:
    pass

def setup_llamaindex_with_hf_model():
    """
    Complete setup for LlamaIndex with Hugging Face models
    """
    
    # Choose your model (all these work without special access)
    model_configs = {
        "qwen2.5-7b": {
            "model_name": "Qwen/Qwen2.5-7B-Instruct",
            "context_window": 32768,
            "max_new_tokens": 2048,
        },
        "qwen2.5-3b": {
            "model_name": "Qwen/Qwen2.5-3B-Instruct", 
            "context_window": 32768,
            "max_new_tokens": 2048,
        },
        "phi3-mini": {
            "model_name": "microsoft/Phi-3-mini-128k-instruct",
            "context_window": 128000,
            "max_new_tokens": 2048,
        },
        "qwen2.5-1.5b": {
            "model_name": "Qwen/Qwen2.5-1.5B-Instruct",
            "context_window": 32768,
            "max_new_tokens": 2048,
        }
    }
    
    # Select your preferred model
    config = model_configs["qwen2.5-7b"]  # Change this as needed
    
    # Setup the LLM
    llm = HuggingFaceLLM(
        model_name=config["model_name"],
        tokenizer_name=config["model_name"],
        context_window=config["context_window"],
        max_new_tokens=config["max_new_tokens"],
        model_kwargs={
            "torch_dtype": torch.float16,
            "trust_remote_code": True,
        },
        generate_kwargs={
            "temperature": 0.1,
            "top_p": 0.9,
            "do_sample": True,
            "repetition_penalty": 1.1,
        },
        device_map="auto",
    )
    
    # Setup embedding model (for RAG)
    embed_model = HuggingFaceEmbedding(
        model_name="BAAI/bge-small-en-v1.5"
    )
    
    # Configure LlamaIndex settings
    Settings.llm = llm
    Settings.embed_model = embed_model
    Settings.chunk_size = 1024
    Settings.chunk_overlap = 200
    
    return llm, embed_model

def create_chatbot_with_documents(document_path="./docs"):
    """
    Create a chatbot that can answer questions about your documents
    """
    # Setup models
    llm, embed_model = setup_llamaindex_with_hf_model()
    
    try:
        # Load documents
        documents = SimpleDirectoryReader(document_path).load_data()
        print(f"Loaded {len(documents)} documents")
        
        # Create index
        index = VectorStoreIndex.from_documents(documents)
        
        # Create query engine
        query_engine = index.as_query_engine(
            response_mode="compact",
            similarity_top_k=3,
        )
        
        return query_engine
        
    except Exception as e:
        print(f"Error loading documents: {e}")
        print("Creating simple chat engine instead...")
        
        # Create simple chat engine without documents
        memory = ChatMemoryBuffer.from_defaults(token_limit=3000)
        chat_engine = SimpleChatEngine.from_defaults(
            llm=llm,
            memory=memory,
            system_prompt="You are a helpful AI assistant. Answer questions clearly and concisely."
        )
        
        return chat_engine

def chat_loop(query_engine):
    """
    Interactive chat loop
    """
    print("Chatbot ready! Type 'quit' to exit.")
    print("-" * 50)
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("Goodbye!")
            break
            
        if not user_input:
            continue
            
        try:
            # Get response
            response = query_engine.query(user_input)
            print(f"\nBot: {response}")
            
        except Exception as e:
            print(f"Error: {e}")
            print("Please try again with a different question.")

if __name__ == "__main__":
    print("Setting up LlamaIndex with Hugging Face model...")
    print("This may take a few minutes on first run (downloading model)...")
    
    # Create chatbot
    query_engine = create_chatbot_with_documents()
    
    # Start chat
    chat_loop(query_engine)
