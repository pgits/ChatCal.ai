import os
from llama_index.llms.groq import Groq

llm = Groq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY")  # Set your GROQ_API_KEY environment variable
)

response = llm.complete("Hello!")
print(response.text)
