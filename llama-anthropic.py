from llama_index.llms.anthropic import Anthropic
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from dotenv import load_dotenv


# Initialize Claude
load_dotenv()

#api_key=os.getenv("ANTHROPIC_API_KEY")
llm = Anthropic(
    model="claude-sonnet-4-20250514",  # Claude Sonnet 4
#api_key="your-api-key-here",  # Or set ANTHROPIC_API_KEY env var
    max_tokens=4096,
    temperature=0.7
)

# Set up local embedding model
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

# Set as default for LlamaIndex
Settings.llm = llm
Settings.embed_model = embed_model

# Now use in your chatbot
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

# Load your documents
documents = SimpleDirectoryReader("/Users/petergits/dev/chatCal.ai").load_data()
index = VectorStoreIndex.from_documents(documents)

# Create chat engine
chat_engine = index.as_chat_engine(
    chat_mode="context",  # or "react", "openai", etc.
    verbose=True
)

# Chat with your bot
response = chat_engine.chat("Your question here")
print(response)
