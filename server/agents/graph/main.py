import os
import json
import re
import asyncio
from langchain_neo4j import Neo4jGraph
from langchain.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import logging
import logging.config
import pandas as pd
import os.path
import numpy as np
from sentence_transformers import SentenceTransformer

# Configure logging
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'file_handler': {
            'level': 'ERROR',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': 'medical_graph_system.log',
            'mode': 'a',
        }
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['default', 'file_handler'],
            'level': 'INFO',
            'propagate': True
        }
    }
})

logger = logging.getLogger(__name__)

load_dotenv()

# Initialize components
graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
    database="medicalrag"
)

llm = ChatGroq(
    model_name="gemma2-9b-it",
    temperature=0.2,
    api_key=os.getenv("GROQ_API_KEY"),
)

class MedicalGraphSystem:
    def __init__(self, session_context: Optional[Dict] = None):
        """Initialize with optional session context"""
        self.session_context = session_context or {}
        self.memory = self._initialize_memory()
        
        # Add CSV fallback functionality
        self.fallback_csv_path = os.path.join(os.path.dirname(__file__), "medical_data.csv")
        self.fallback_data = self._load_fallback_csv()
        
        # Initialize embedding model for semantic search in fallback
        try:
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            self.column_embeddings = self._cache_column_embeddings()
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            self.embedding_model = None
            self.column_embeddings = {}

    def _initialize_memory(self) -> ConversationBufferMemory:
        """Initialize memory with session context if available"""
        memory = ConversationBufferMemory()
        
        # Load previous conversation if exists in session
        if "chat_history" in self.session_context:
            for exchange in self.session_context["chat_history"]:
                memory.chat_memory.add_user_message(exchange["query"])
                memory.chat_memory.add_ai_message(exchange["response"])
        
        return memory

    def _load_fallback_csv(self) -> Optional[pd.DataFrame]:
        """Load fallback CSV data if available"""
        try:
            if os.path.exists(self.fallback_csv_path):
                logger.info(f"Loading fallback CSV data from: {self.fallback_csv_path}")
                return pd.read_csv(self.fallback_csv_path)
            else:
                logger.warning(f"Fallback CSV not found at: {self.fallback_csv_path}")
                return None
        except Exception as e:
            logger.error(f"Error loading fallback CSV: {e}")
            return None

    def _cache_column_embeddings(self) -> Dict:
        """Cache embeddings for CSV columns to speed up matching"""
        embeddings = {}
        if self.fallback_data is None or self.embedding_model is None:
            return embeddings
            
        try:
            for column in self.fallback_data.columns:
                embeddings[column] = self.embedding_model.encode(column.replace('_', ' '))
            return embeddings
        except Exception as e:
            logger.error(f"Error caching column embeddings: {e}")
            return {}

    def clean_cypher_query(self, query: str) -> str:
        """Clean and validate Cypher queries"""
        # Remove markdown code blocks if present
        if query.startswith("```cypher"):
            query = query[9:]  # Remove ```cypher
        if query.endswith("```"):
            query = query[:-3]  # Remove ```
        
        # Fix common syntax issues
        query = query.strip()
        query = query.replace('"', "'")  # Standardize quotes
        query = query.replace("SYMPTOMM_OF", "SYMPTOM_OF")  # Fix relationship typo
        
        # Ensure query ends with semicolon
        if not query.endswith(";"):
            query += ";"
        
        return query

    def execute_query_with_hybrid_matching(self, query: str, original_query: str) -> Any:
        """
        Perform hybrid matching with CSV fallback when no results found.
        
        Args:
            query: The Cypher query to execute
            original_query: The original user's natural language query
        
        Returns:
            Query results or semantic search fallback or CSV fallback
        """
        print("\n=== 🛠️ Starting execute_query_with_hybrid_matching ===")
        print(f"Original query: {query}")
        
        # Clean the query first
        query = self.clean_cypher_query(query)
        modified_query = query
        
        try:
            # First, attempt to execute the original query
            query_result = graph.query(modified_query)
            
            # If query returns results, return them
            if query_result:
                print("=== 🛠️ Direct query successful ===")
                return query_result
            
            # If no results, prepare for semantic fallback
            print("⚠️ No direct results found. Initiating semantic search fallback.")
            
            # Extract entity names from the original query
            entity_matches = re.findall(r"['\"]([^'\"]+)['\"]", query)
            
            # If no entities found, use the entire original query
            search_terms = entity_matches if entity_matches else [original_query]
            
            # Perform semantic search for each term
            semantic_results = []
            for term in search_terms:
                # Try semantic matching across different node types
                node_types = ['Symptom', 'Disease', 'Drug', 'Treatment']
                type_matches = []
                
                for node_type in node_types:
                    matches = self.find_semantic_matches(term, node_type)
                    if matches:
                        type_matches.extend(matches)
                
                if type_matches:
                    # Sort matches by similarity
                    type_matches.sort(key=lambda x: x[2], reverse=True)
                    
                    # Prepare detailed semantic search result
                    best_match = type_matches[0]
                    semantic_result = {
                        "original_search": term,
                        "best_match": {
                            "name": best_match[0],
                            "node_type": best_match[1],
                            "similarity": best_match[2]
                        },
                        "related_info": [
                            {"name": match[0], "type": match[1], "similarity": match[2]} 
                            for match in type_matches[1:5]  # Top 5 related matches
                        ]
                    }
                    semantic_results.append(semantic_result)
            
            # Return semantic search results if found
            if semantic_results:
                print(f"🔍 Semantic matches found: {len(semantic_results)}")
                return semantic_results
            
            # If no semantic matches, try CSV fallback
            print("📄 No semantic matches found. Trying CSV fallback...")
            csv_fallback = self._query_fallback_csv(original_query)
            
            if csv_fallback["status"] == "success":
                print(f"✅ CSV fallback found relevant information in columns: {csv_fallback['relevant_columns']}")
                return {
                    "type": "csv_fallback",
                    "data": csv_fallback
                }
            
            # If no matches at all, return None
            print("❌ No matches found in any source.")
            return None
            
        except Exception as e:
            print(f"⚠️ Query execution failed: {str(e)}")
            # Try CSV fallback on exception
            try:
                csv_fallback = self._query_fallback_csv(original_query)
                if csv_fallback["status"] == "success":
                    return {
                        "type": "csv_fallback",
                        "data": csv_fallback
                    }
            except:
                pass
            return None

    def find_semantic_matches(self, term: str, node_type: str) -> list:
        """
        Find semantic matches for a given term and node type.
        
        Args:
            term: The search term
            node_type: The node type to search
        
        Returns:
            List of tuples containing the matched node name, node type, and similarity score
        """
        # Implement semantic search logic here
        # For demonstration purposes, return dummy matches
        return [
            ("Match 1", node_type, 0.8),
            ("Match 2", node_type, 0.7),
            ("Match 3", node_type, 0.6)
        ]

    def _query_fallback_csv(self, user_query: str) -> Dict[str, Any]:
        """
        Query the fallback CSV when no results are found in graph database
        
        Args:
            user_query: The user's question text
            
        Returns:
            Dict with structured results or error message
        """
        if self.fallback_data is None or self.embedding_model is None:
            return {"status": "error", "message": "Fallback data or embedding model not available"}
            
        try:
            # Encode the query
            query_embedding = self.embedding_model.encode(user_query)
            
            # Find relevant columns
            column_scores = {}
            for column, embedding in self.column_embeddings.items():
                similarity = np.dot(query_embedding, embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
                )
                column_scores[column] = float(similarity)
            
            # Get top relevant columns (similarity > 0.3)
            sorted_columns = sorted(column_scores.items(), key=lambda x: x[1], reverse=True)
            top_columns = [col for col, score in sorted_columns if score > 0.3][:3]
            
            if not top_columns:
                return {"status": "no_match", "message": "No relevant information found in CSV"}
            
            # Extract information from those columns
            relevant_data = {}
            for column in top_columns:
                # Get non-empty values from column
                values = self.fallback_data[column].dropna().tolist()
                relevant_data[column] = values[:5]  # Get up to 5 values
            
            return {
                "status": "success",
                "relevant_columns": top_columns,
                "column_scores": {col: column_scores[col] for col in top_columns},
                "data": relevant_data
            }
            
        except Exception as e:
            logger.error(f"Error querying fallback CSV: {e}")
            return {"status": "error", "message": str(e)}

    def _format_csv_fallback_response(self, fallback_result: Dict) -> str:
        """Format CSV fallback results into a natural language response"""
        if fallback_result["status"] != "success":
            return "I couldn't find specific information about that in our database."
        
        # Get the formatted column names and data
        response_parts = ["Based on our medical records:"]
        
        for column in fallback_result["relevant_columns"]:
            formatted_column = column.replace("_", " ").title()
            values = fallback_result["data"][column]
            
            response_parts.append(f"\n• {formatted_column}:")
            for value in values:
                response_parts.append(f"  - {value}")
        
        response_parts.append("\nThis information is based on our general medical database. For personalized medical advice, please consult with your healthcare provider.")
        
        return "\n".join(response_parts)

    async def handle_query(self, query_data: Dict) -> Dict:
        """
        Handle medical graph queries with session context and CSV fallback
        """
        try:
            user_question = query_data.get("text", "")
            self.session_context = query_data.get("context", {})
            
            if user_question.lower() in ['exit', 'quit', 'bye']:
                self.memory.clear()
                return {
                    "response": "Thank you for contacting Osaka University Hospital. Have a good day!",
                    "context_updates": {},
                    "suggested_next": None
                }
                
            examples = [
                {"question": "How many diseases are there?", "query": "MATCH (d:Disease) RETURN count(d);"},
                {"question": "Symptoms of COVID-19?", "query": "MATCH (s:Symptom)-[:SYMPTOM_OF]->(d:Disease {{name: 'COVID-19'}}) RETURN s.name;"},
                {"question": "Drugs for Diabetes?", "query": "MATCH (d:Disease {{name: 'Diabetes'}})<-[:PRESCRIBED_FOR]-(drug:Drug) RETURN drug.name;"},
            ]

            schema = """Node properties:
Disease {name: STRING}, Symptom {name: STRING}, GeneticLinkage {name: STRING}, 
CareInstruction {name: STRING}, Drug {name: STRING}, Treatment {name: STRING}, 
SideEffect {name: STRING}.

Relationships:
(:Symptom)-[:SYMPTOM_OF]->(:Disease), 
(:GeneticLinkage)-[:LINKED_TO]->(:Disease), 
(:CareInstruction)-[:RECOMMENDED_FOR]->(:Disease), 
(:Drug)-[:PRESCRIBED_FOR]->(:Disease), 
(:Drug)-[:RECOMMENDED_DOSAGE]->(:Disease), 
(:Treatment)-[:TREATS]->(:Disease), 
(:Treatment)-[:USES_DRUG]->(:Drug), 
(:Treatment)-[:HAS_SIDE_EFFECT]->(:SideEffect)."""

            example_prompt = PromptTemplate.from_template(
                "User input: {question}\nCypher query: {query}"
            )

            prompt = FewShotPromptTemplate(
                examples=examples,
                example_prompt=example_prompt,
                prefix="""You are a Neo4j expert. Generate ONLY the Cypher query - no additional text or markdown. 

Important rules:
1. Always use single quotes for string values
2. Always end queries with a semicolon
3. Never include markdown code blocks
4. Use correct relationship types from schema

Schema:
{schema}

Examples:""",
                suffix="User input: {question}\nCypher query:",
                input_variables=["question", "schema"],
            )

            # Generate Cypher query
            formatted_prompt = prompt.format(
                question=user_question,
                schema=schema
            )
            response = await llm.ainvoke(formatted_prompt)
            
            if not response or not hasattr(response, 'content'):
                return {
                    "response": "I couldn't generate a proper query for that question.",
                    "context_updates": {},
                    "suggested_next": None
                }

            generated_query = response.content
            print(f"\nGenerated query before cleaning: {generated_query}")
            generated_query = self.clean_cypher_query(generated_query)
            print(f"Cleaned query: {generated_query}")

            query_result = self.execute_query_with_hybrid_matching(generated_query, user_question)

            if not query_result:
                return {
                    "response": "I couldn't find any information about that in our database.",
                    "context_updates": {},
                    "suggested_next": "HUMAN"
                }
                
            # Check if result is from CSV fallback
            if isinstance(query_result, dict) and query_result.get("type") == "csv_fallback":
                csv_response = self._format_csv_fallback_response(query_result["data"])
                
                # Update conversation memory
                self.memory.chat_memory.add_user_message(user_question)
                self.memory.chat_memory.add_ai_message(csv_response)
                
                return {
                    "response": csv_response,
                    "context_updates": {
                        "last_interaction": datetime.now().isoformat(),
                        "data_source": "csv_fallback",
                        "chat_history": [
                            {
                                "query": user_question,
                                "response": csv_response,
                                "timestamp": datetime.now().isoformat()
                            }
                        ]
                    },
                    "suggested_next": None
                }

            # Generate natural language response
            response_prompt = f"""You are a Clinical Triage agent for Osaka University Hospital. 
Explain these results in simple, compassionate terms:

Question: {user_question}
Results: {json.dumps(query_result, indent=2)}

Response:"""
            
            final_response = await llm.ainvoke(response_prompt)
            
            # Update conversation memory and context
            self.memory.chat_memory.add_user_message(user_question)
            self.memory.chat_memory.add_ai_message(final_response.content)
            
            context_updates = {
                "last_interaction": datetime.now().isoformat(),
                "chat_history": [
                    {
                        "query": user_question,
                        "response": final_response.content,
                        "timestamp": datetime.now().isoformat()
                    }
                ]
            }
            
            return {
                "response": final_response.content,
                "context_updates": context_updates,
                "suggested_next": None
            }
            
        except Exception as e:
            self.memory.clear()
            # Try CSV fallback on exception
            try:
                csv_fallback = self._query_fallback_csv(user_question)
                if csv_fallback["status"] == "success":
                    csv_response = self._format_csv_fallback_response(csv_fallback)
                    return {
                        "response": csv_response,
                        "context_updates": {"data_source": "csv_fallback"},
                        "suggested_next": None
                    }
            except:
                pass
                
            return {
                "response": f"⚠️ An error occurred: {str(e)}",
                "context_updates": {},
                "suggested_next": "HUMAN"
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
        graph_system = MedicalGraphSystem(query_data.get("context", {}))
        return await graph_system.handle_query(query_data)
    except Exception as e:
        return {
            "response": f"Medical knowledge system error: {str(e)}",
            "context_updates": {},
            "suggested_next": "HUMAN"
        }

# Preserve original main for testing
def main():
    """Standalone testing mode"""
    print("""
    ┌───────────────────────────────────────────────────────────────┐
    │          Osaka University Hospital - Clinical Triage          │
    │                   Automated Call Center System                │
    └───────────────────────────────────────────────────────────────┘
    Type 'exit' to end the conversation.
    """)

    async def async_main():
        graph_system = MedicalGraphSystem()
        
        while True:
            try:
                user_input = input("\nPatient: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("\nThank you for contacting Osaka University Hospital. Have a good day!")
                    break
                    
                if not user_input:
                    print("Please enter a valid question.")
                    continue

                response = await graph_system.handle_query({"text": user_input})
                print(f"\nAssistant: {response['response']}")
                
            except KeyboardInterrupt:
                print("\n\nSession ended by user. Goodbye!")
                break

    asyncio.run(async_main())

# Factory method for router compatibility
async def get_agent() -> MedicalGraphSystem:
    """Get the agent instance for routing system"""
    if 'graph_agent_instance' not in globals():
        global graph_agent_instance
        graph_agent_instance = MedicalGraphSystem()
    return graph_agent_instance

# Add initialize method to MedicalGraphSystem for router compatibility
def initialize(self) -> None:
    """Initialization method for router compatibility"""
    # Already initialized in __init__
    return

MedicalGraphSystem.initialize = initialize

if __name__ == "__main__":
    print("=== 🚀 Starting application ===")
    main()