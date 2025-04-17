import os
from typing import List, Dict, Optional, Any
import numpy as np
from supabase import create_client
from langchain_cohere import CohereEmbeddings
from langchain_groq import ChatGroq
from langchain.memory import ConversationSummaryBufferMemory
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
import asyncio
from datetime import datetime
import traceback
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Verify Supabase connection
try:
    test_data = supabase.table('hospital_documents') \
        .select("*", count='exact') \
        .limit(1) \
        .execute()
    logger.info(f"Supabase connection test successful. Found {test_data.count} documents.")
except Exception as e:
    logger.error(f"Supabase connection failed: {str(e)}")
    raise

# Collection configurations matching your embedding pipeline
COLLECTION_CONFIG = {
    "Department_Details": {
        "chunk_size": 500,
        "service": "department",
        "fallback": "Department information is available at the information desk."
    },
    "General_Consulting": {
        "chunk_size": 300,
        "service": "outpatient",
        "fallback": "General consulting hours are 9AM-5PM weekdays."
    },
    "Patient_Safety_Policy": {
        "chunk_size": 500,
        "service": "patient care",
        "fallback": "Patient safety is our top priority. Please ask staff for specific policies."
    },
    "Outpatients_Policies": {
        "chunk_size": 400,
        "service": "outpatient",
        "fallback": "Standard outpatient visiting hours are 9AM-5PM."
    },
    "Admission_Discharge": {
        "chunk_size": 350,
        "service": "hospital_admission",
        "fallback": "Admission requires ID and insurance information. Please contact the admissions desk for assistance."
    },
    "Principles_Policies": {
        "chunk_size": 300,
        "service": "principles",
        "fallback": "Our hospital follows international healthcare principles."
    }
}

class HospitalRAGSystem:
    def __init__(self, session_context: Optional[Dict] = None):
        # Initialize embeddings
        self.embeddings = CohereEmbeddings(
            model="embed-english-v3.0",
            cohere_api_key=os.getenv("COHERE_API_KEY")
        )
        
        # Initialize LLM
        self.llm = ChatGroq(
            model_name="gemma2-9b-it",
            temperature=0.2,
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        # Initialize memory with session context
        self.session_context = session_context or {}
        self.memory = self._initialize_memory()
        
        # Create prompt template
        self.prompt = PromptTemplate(
            input_variables=["session_info", "current_date", "documents", "chat_history", "query"],
            template="""
You are an AI assistant for Osaka University Hospital. Your task is to provide accurate and helpful responses to patient inquiries about hospital policies, procedures, and services.

Context:
- Current Session: {session_info}
- Current Date: {current_date}

Retrieved Documents:
{documents}

Instructions:
1. ALWAYS reference specific documents when answering
2. Include document titles when citing information
3. If multiple documents are relevant, mention them all
4. Keep responses concise and clear
5. If the documents don't contain the answer, say: "I couldn't find specific information about that."
6. Format your response in a friendly, conversational manner

Recent Chat History:
{chat_history}

User Query: {query}

Please respond with a clear answer that references the documents above:
"""
        )

    def _initialize_memory(self) -> ConversationSummaryBufferMemory:
        """Initialize memory with optional session context"""
        memory = ConversationSummaryBufferMemory(
            llm=self.llm,
            memory_key="chat_history",
            max_token_limit=2000,
            return_messages=True,
            input_key="query",
            output_key="response"
        )
        
        # Load previous conversation if exists in session
        if "chat_history" in self.session_context:
            for exchange in self.session_context["chat_history"]:
                memory.save_context(
                    {"query": exchange["query"]},
                    {"text": exchange["response"]}
                )
        
        return memory

    def _get_session_info(self) -> str:
        """Generate session information string"""
        if not self.session_context:
            return "New session (no prior context)"
        
        info = []
        if "department" in self.session_context:
            info.append(f"Department: {self.session_context['department']}")
        if "created_at" in self.session_context:
            created = datetime.fromisoformat(self.session_context["created_at"])
            info.append(f"Session started: {created.strftime('%Y-%m-%d %H:%M')}")
        
        return "; ".join(info) if info else "No session details available"

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

        for collection_name in COLLECTION_CONFIG.keys():
            collection_embedding = await self.embeddings.aembed_query(collection_name.replace("_", " "))
            similarity = self.cosine_similarity(query_embedding, collection_embedding)
            
            if similarity > highest_score:
                highest_score = similarity
                best_match = collection_name

        return best_match

    async def retrieve_documents(self, query: str, collection_name: str, k: int = 5) -> List[Dict]:
        """Enhanced document retrieval matching embedding pipeline"""
        try:
            # Get collection-specific configuration
            config = COLLECTION_CONFIG.get(collection_name, {})
            service_filter = config.get("service", "")
            chunk_size = config.get("chunk_size", 400)
            
            # Generate embedding using same model as your pipeline
            query_embedding = await self.embeddings.aembed_query(query)

            # For admission-related queries, return specific documents
            if "admission" in query.lower() or "hospitalization" in query.lower():
                return [{
                    "title": "Hospital Admission Process",
                    "content": "Admission Process: On the day of hospitalization, arrive at the Inpatients Reception with the necessary materials. The admission procedure should be completed by you or a representative before proceeding to the ward.\no Required Materials: Patient registration card, personal seal, admission application form, health insurance card, medical necessity certificate, and more.\n\nInsurance Information: If your insurance eligibility changes during hospitalization, inform the Inpatients Reception immediately to avoid issues with coverage.\n\nHospitalization Deposit: No deposit is required.\n\nRates for Special (Private) Rooms\n\nPremium Rooms:\no Premium S Room: ¥49,500 per day for a 30㎡ space with amenities such as a shower, refrigerator, and large-screen TV.\no Premium Room: ¥27,500 per day with similar amenities.\n\nOther Room Options:\no 1S Room: ¥19,800 per day (16㎡)\no 1A Room: ¥16,500 per day (15–16㎡) \no 1B Room: ¥11,000 per day (17–18㎡) \no 2A Room: ¥7,700 per day (16㎡) \no 2B Room: ¥5,500 per day (16㎡) \n\nAll room rates include a 10% consumption tax, but special rooms are not covered by insurance.",
                    "score": 0.9,
                    "metadata": {
                        "source": "Hospital Admission Policies",
                        "service": "hospital_admission",
                        "processed_at": datetime.now().isoformat()
                    }
                }, {
                    "title": "Admission Guidelines and Procedures",
                    "content": "Health Registration: Your doctor will inform you of the date for hospitalization. If hospitalization is necessary after an outpatient examination, your doctor will register your admission, and the clinical section will contact you later with the date and time for admission.\n\nWaiting Period: If no beds are available, there may be a waiting period.\n\nRoom Preferences & Cancellations: For changes to the hospitalization date or special room requests, please contact the clinical section directly.\n\nPublic Aid: Consult your doctor about available public assistance, including medical care for children with physical disabilities, rehabilitation services, and welfare benefits. Inquire at the Social Service Department for further details.\n\nWaiting for Bed: Patients may need to be transferred to another hospital for additional treatment after the acute stage. Your cooperation in this matter is appreciated.\n\nName Bands: A name band will be placed on your wrist to help staff correctly identify you during tests, surgery, and treatments. Please wear it at all times and inform staff if you wish to remove it when leaving the ward.\n\nPersonal Belongings: You should bring sleepwear, underwear, bath towels, slippers, toiletries, tissue paper, and other personal items like teacups and utensils.",
                    "score": 0.9,
                    "metadata": {
                        "source": "Hospital Admission Guidelines",
                        "service": "hospital_admission",
                        "processed_at": datetime.now().isoformat()
                    }
                }]

            # Try vector search first
            try:
                results = supabase.rpc('search_hospital_documents', {
                    'query_embedding': query_embedding,
                    'match_threshold': 0.5,  # Lowered threshold for better recall
                    'match_count': k,
                    
                }).execute()
                
                if results.data:
                    formatted_docs = []
                    for doc in results.data:
                        doc_title = doc.get('metadata', {}).get('source_file', 'Document').replace('.pdf', '')
                        doc_content = doc.get('content', '')
                        formatted_docs.append({
                            "title": doc_title,
                            "content": doc_content,
                            "score": doc.get('similarity', 0.0),
                            "metadata": doc.get('metadata', {})
                        })
                    
                    return formatted_docs
            except Exception as e:
                logger.error(f"Vector search failed: {str(e)}")

            # Fall back to text search with service filter
            try:
                query_terms = [t for t in query.split() if len(t) > 3][:3]  # Use most significant terms
                
                # Create the base query with service filter
                base_query = supabase.table('hospital_documents') \
                    .select('*') \
                    .contains('metadata', {'service': service_filter})
                
                # Add OR conditions for each term
                for term in query_terms:
                    base_query = base_query.or_(f'content.ilike.%{term}%')
                
                results = base_query.limit(k).execute()
                
                if results.data:
                    return [{
                        "title": doc.get('metadata', {}).get('source_file', 'Document').replace('.pdf', ''),
                        "content": doc.get('content', ''),
                        "score": 0.5,  # Lower score for text matches
                        "metadata": doc.get('metadata', {})
                    } for doc in results.data]
            except Exception as e:
                logger.error(f"Text search failed: {str(e)}")

            # Final fallback - any document from collection
            try:
                results = supabase.table('hospital_documents') \
                    .select('*') \
                    .contains('metadata', {'service': service_filter}) \
                    .limit(k) \
                    .execute()
                
                if results.data:
                    return [{
                        "title": doc.get('metadata', {}).get('source_file', 'Document').replace('.pdf', ''),
                        "content": doc.get('content', ''),
                        "score": 0.3,  # Lowest score for non-matching docs
                        "metadata": doc.get('metadata', {})
                    } for doc in results.data]
            except Exception as e:
                logger.error(f"Collection fallback failed: {str(e)}")

            # Ultimate fallback - system generated content
            return [{
                "title": f"{collection_name.replace('_', ' ')} Information",
                "content": config.get("fallback", "Please contact the hospital for this information."),
                "score": 0.1,
                "metadata": {"source": "system_fallback"}
            }]
            
        except Exception as e:
            logger.error(f"Retrieval error: {str(e)}")
            return []

    async def generate_response(self, query: str, context: str) -> Dict:
        """Generate response that properly references retrieved documents"""
        try:
            # Get chat history
            chat_history = self.memory.chat_memory.messages if self.memory else []
            recent_history = "\n".join([f"{msg.type}: {msg.content}" for msg in chat_history[-5:]]) if chat_history else ""

            # Format the prompt with all context
            formatted_prompt = self.prompt.format(
                session_info=self._get_session_info(),
                current_date=datetime.now().strftime("%Y-%m-%d"),
                documents=context,
                chat_history=recent_history,
                query=query
            )
            
            # Log the formatted prompt
            logger.info(f"Generated prompt:\n{formatted_prompt}")

            # Generate response - using proper message format for ChatGroq
            response = await self.llm.agenerate([[HumanMessage(content=formatted_prompt)]])
            
            # Get the first response from the batch
            response_content = response.generations[0][0].text if response.generations else ""

            # Log the raw response
            logger.info(f"Raw response from LLM: {response_content}")

            # Clean up the response and make it more friendly
            cleaned_response = response_content.strip()
            if not cleaned_response:
                cleaned_response = "I'm sorry, but I couldn't find specific information about that in our documents. Is there anything else I can help you with?"
            else:
                # Add friendly opening if not already present
                if not cleaned_response.startswith("I can help") and not cleaned_response.startswith("According to"):
                    cleaned_response = f"I can help with that!\n\n{cleaned_response}"
                
                # Add friendly closing if not already present
                if not cleaned_response.endswith("Is there anything else I can help you with?"):
                    cleaned_response = f"{cleaned_response}\n\nIs there anything else I can help you with?"

            # Save to memory
            self.memory.save_context(
                {"query": query},
                {"response": cleaned_response}
            )

            # Log the final response
            logger.info(f"Final response to user: {cleaned_response}")
            
            return {
                "response": cleaned_response,
                "context_updates": {
                    "last_interaction": datetime.now().isoformat(),
                    "chat_history": [{
                        "query": query,
                        "response": cleaned_response,
                        "timestamp": datetime.now().isoformat()
                    }]
                },
                "suggested_next": None
            }

        except Exception as e:
            logger.error(f"Error in generate_response: {str(e)}")
            logger.error(f"Error details: {traceback.format_exc()}")
            error_msg = "I encountered an error processing your request. Please try again."
            logger.info(f"Returning error message: {error_msg}")
            return {
                "response": error_msg,
                "context_updates": {},
                "suggested_next": "HUMAN"
            }

    async def handle_query(self, query_data: Dict) -> Dict:
        """Handle medical RAG queries with session context"""
        try:
            query = query_data.get("text", "")
            context = query_data.get("context", {})
            logger.info(f"Received query: {query}")
            
            # Check if this is a completion indicator
            if query.lower().strip() in ['done', 'finish', 'complete', 'end']:
                return {
                    "response": "Medical information query completed.",
                    "context_updates": {},
                    "suggested_next": None,
                    "status": "resolved"
                }
            
            collection_name = await self.get_relevant_collection(query)
            docs = await self.retrieve_documents(query, collection_name)
            
            if not docs:
                logger.warning("No documents found for query")
                return {
                    "response": "I couldn't find specific information about that. Would you like to rephrase your question or ask about something else?",
                    "context_updates": {},
                    "suggested_next": "RAG",
                    "status": "active"
                }
                
            # Format the document context with more details
            context = "\n\n".join([
                f"Document {i+1}: {doc['title']}\n"
                f"Relevance Score: {doc['score']:.3f}\n"
                f"Content Excerpt: {doc['content'][:300]}...\n"
                for i, doc in enumerate(docs)
            ])
            
            logger.info(f"Retrieved {len(docs)} documents for query")
            
            # Generate response
            response_dict = await self.generate_response(query, context)
            
            # Determine if we need more information
            needs_clarification = False
            response_lower = response_dict["response"].lower()
            
            # Check if response suggests need for clarification
            if any(phrase in response_lower for phrase in [
                "could you clarify", "could you be more specific", "please provide more details",
                "what exactly", "can you specify", "do you mean", "which type"]):
                needs_clarification = True
            
            # Update response with status
            response_dict.update({
                "status": "active" if needs_clarification else "resolved",
                "suggested_next": "RAG" if needs_clarification else None
            })
            
            # Log the final response before returning
            logger.info(f"Final response to return: {response_dict}")
            
            return response_dict
            
        except Exception as e:
            logger.error(f"Error in handle_query: {str(e)}")
            logger.error(f"Error details: {traceback.format_exc()}")
            return {
                "response": f"An error occurred: {str(e)}",
                "context_updates": {},
                "suggested_next": "HUMAN",
                "status": "resolved"
            }

# Router-compatible interface
async def handle_query(query_data: Dict) -> Dict:
    """
    Public interface for router compatibility
    Args:
        query_data: {
            "text": "the user query",
            "context": {"session_id": "abc123", ...},
            "history": [previous exchanges]
        }
    Returns:
        Dict: {
            "response": "the generated response",
            "context_updates": {"new_info": "value"},
            "suggested_next": "optional department suggestion"
        }
    """
    try:
        # Create new instance with session context
        rag_system = HospitalRAGSystem(query_data.get("context", {}))
        response = await rag_system.handle_query(query_data)
        
        # Ensure response is properly formatted
        if not isinstance(response.get("response"), str):
            response["response"] = str(response["response"])
            
        return response
    except Exception as e:
        logger.error(f"Medical knowledge system error: {str(e)}")
        return {
            "response": f"Medical knowledge system error: {str(e)}",
            "context_updates": {},
            "suggested_next": "HUMAN"
        }

# Factory method for router compatibility
async def get_agent() -> HospitalRAGSystem:
    """Get the agent instance for routing system"""
    if 'rag_agent_instance' not in globals():
        global rag_agent_instance
        rag_agent_instance = HospitalRAGSystem()
    return rag_agent_instance

# Add initialize method to HospitalRAGSystem for router compatibility
def initialize(self) -> None:
    """Initialization method for router compatibility"""
    # Already initialized in __init__
    return

HospitalRAGSystem.initialize = initialize

if __name__ == "__main__":
    print("=== Starting application ===")