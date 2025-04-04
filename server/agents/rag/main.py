import os
from typing import List, Dict, Optional
import numpy as np
from supabase import create_client
from langchain_cohere import CohereEmbeddings
from langchain_groq import ChatGroq
from langchain.memory import ConversationSummaryBufferMemory
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Collection mapping for topic selection
COLLECTIONS = {
    "Department_Details": "Department_Details",
    "General_Consulting": "General_Consulting",
    "Patient_Safety_Policy": "Patient_Safety_Policy",
    "Outpatients_Policies": "Outpatients_Policies",
    "Admission_Discharge": "Admission_Discharge",
    "Principles_Policies": "Principles_Policies"
}

class HospitalRAGSystem:
    def __init__(self):
        # Initialize embeddings
        self.embeddings = CohereEmbeddings(
            model="embed-english-v3.0",
            cohere_api_key=os.getenv("COHERE_API_KEY")
        )
        
        # Initialize LLM
        self.llm = ChatGroq(
            model_name="gemma2-9b-it",
            temperature=0,
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
        
        # Initialize memory
        self.memory = ConversationSummaryBufferMemory(
            llm=ChatGroq(
                model_name="gemma2-9b-it",
                temperature=0,
                groq_api_key=os.getenv("GROQ_API_KEY")
            ),
            memory_key="chat_history",
            max_token_limit=2000,
            return_messages=True
        )
        
        # System prompt
        self.system_prompt = """You are an AI RAG Agent for Osaka University Hospital. Your task is to answer questions about hospital policies, departments, admission procedures, patient rights, and consulting services. 

Use the provided context to answer accurately. If the context is insufficient, say: "I need more information." Keep responses concise, as if speaking to a patient on a call. Always reference retrieved documents when possible."""

        # Setup the prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self.system_prompt),
            HumanMessagePromptTemplate.from_template(
                """Recent Chat History:
{chat_history}

User Query: {query}

Context:
{context}

Response:"""
            )
        ])

    def cosine_similarity(self, vecA: List[float], vecB: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vecA, vecB)
        magnitudeA = np.linalg.norm(vecA)
        magnitudeB = np.linalg.norm(vecB)
        return dot_product / (magnitudeA * magnitudeB)

    async def get_relevant_collection(self, query: str) -> str:
        """Determine the most relevant collection using embeddings"""
        query_embedding = await self.embeddings.aembed_query(query)
        best_match = "Admission_Discharge"  # Default collection
        highest_score = -1

        for collection_name, collection_id in COLLECTIONS.items():
            collection_embedding = await self.embeddings.aembed_query(collection_name.replace("_", " "))
            similarity = self.cosine_similarity(query_embedding, collection_embedding)
            
            if similarity > highest_score:
                highest_score = similarity
                best_match = collection_id

        return best_match

    async def retrieve_documents(self, query: str, collection_name: str, k: int = 5) -> List[Dict]:
        """Retrieve relevant documents from Supabase using vector search"""
        query_embedding = await self.embeddings.aembed_query(query)
        embedding_list = query_embedding.tolist() if hasattr(query_embedding, 'tolist') else list(query_embedding)
        
        results = supabase.rpc('search_hospital_documents', {
            'query_embedding': embedding_list,
            'match_threshold': 0.7,
            'match_count': k,
            'collection_name': collection_name
        }).execute()
        
        return results.data if results.data else []

    async def generate_response(self, query: str, context: str) -> str:
        """Generate response using the new Runnable approach"""
        # Get chat history
        memory_vars = self.memory.load_memory_variables({})
        chat_history = memory_vars.get("chat_history", [])
        recent_history = "\n".join([f"{msg.type}: {msg.content}" for msg in chat_history[-5:]]) if chat_history else ""
        
        # Create the chain
        chain = (
            RunnablePassthrough.assign(
                chat_history=lambda _: recent_history,
                context=lambda _: context
            )
            | self.prompt
            | self.llm
        )
        
        # Invoke the chain
        response = await chain.ainvoke({"query": query})
        
        return response.content

    async def handle_query(self, query: str) -> str:
        """Handle RAG queries programmatically for router integration"""
        try:
            if query.lower() == "exit":
                self.memory.clear()
                return "Goodbye! Have a nice day."
            
            collection_name = await self.get_relevant_collection(query)
            docs = await self.retrieve_documents(query, collection_name)
            context = "\n".join([f"{i+1}. {doc['content']}" for i, doc in enumerate(docs)]) if docs else "No relevant documents found."
            
            response = await self.generate_response(query, context)
            self.memory.save_context({"query": query}, {"text": response})
            
            return response
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.memory.clear()
            return f"Sorry, I encountered an error: {str(e)}"

# Router-compatible interface
async def handle_query(query: str) -> str:
    """
    Public interface for router compatibility
    Args:
        query (str): The user's query
    Returns:
        str: The agent's response
    """
    try:
        # Create new instance for each query to ensure clean state
        rag_system = HospitalRAGSystem()
        response = await rag_system.handle_query(query)
        return response
    except Exception as e:
        return f"Information system error: {str(e)}. Please try again later."

# Preserve original chat loop for testing
async def chat_loop():
    """Standalone testing mode"""
    rag_system = HospitalRAGSystem()
    print("Hospital RAG Agent (Standalone Mode)")
    print("Type 'exit' to quit\n")
    
    while True:
        try:
            query = input("\nUser: ").strip()
            if not query:
                continue
                
            if query.lower() == "exit":
                print("Goodbye!")
                break
                
            response = await rag_system.handle_query(query)
            print(f"\nRAG Agent: {response}")
            
        except KeyboardInterrupt:
            print("\nSession ended by user")
            break

if __name__ == "__main__":
    asyncio.run(chat_loop())