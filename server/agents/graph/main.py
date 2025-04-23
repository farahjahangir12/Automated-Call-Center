import os
import json
import re
import asyncio
from langchain_neo4j import Neo4jGraph
from langchain.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import logging.config

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
        
    def _initialize_memory(self) -> ConversationBufferMemory:
        """Initialize memory with session context if available"""
        memory = ConversationBufferMemory()
        
        # Load previous conversation if exists in session
        if "chat_history" in self.session_context:
            for exchange in self.session_context["chat_history"]:
                memory.chat_memory.add_user_message(exchange["query"])
                memory.chat_memory.add_ai_message(exchange["response"])
        
        return memory

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
        Perform hybrid matching (fuzzy + semantic) before executing the query.
        
        Args:
            query: The Cypher query to execute
            original_query: The original user's natural language query
        
        Returns:
            Query results or semantic search fallback
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
            
            # If no semantic matches, return None
            print("❌ No semantic matches found.")
            return None
        
        except Exception as e:
            print(f"⚠️ Query execution failed: {str(e)}")
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

    async def handle_query(self, query_data: Dict) -> Dict:
        """
        Handle medical graph queries with session context
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