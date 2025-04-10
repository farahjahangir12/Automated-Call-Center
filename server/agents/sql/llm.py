import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize LLM using Groq
llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,  
    model_name="llama-3.3-70b-versatile",
    temperature=0.2,
    max_tokens=1000,
    max_retries=3,
    timeout=30.0
)
__all__ = ["llm"]

# # Function to return the LLM instance
# def get_llm():
#     return llm