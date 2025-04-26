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
        """Initialize with generic context tracking"""
        self.session_context = session_context or {
            'active_entities': [],  # Track all entity mentions
            'last_query_type': None,
            'query_history': []
        }
        
        # Add embedding model initialization
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Define node types for semantic search
        self.node_types = {
            'symptoms': {'labels': ['Symptom'], 'relations': ['SYMPTOM_OF']},
            'conditions': {'labels': ['Disease'], 'relations': ['TREATS', 'PRESCRIBED_FOR']},
            'treatments': {'labels': ['Treatment'], 'relations': ['HAS_SIDE_EFFECT']},
            'drugs': {'labels': ['Drug'], 'relations': ['RECOMMENDED_DOSAGE']}
        }

    def _extract_entities(self, text: str) -> list:
        """
        Generic entity extraction using semantic search
        
        Args:
            text: User's input text
        
        Returns:
            List of extracted entities with type, name, and similarity score
        """
        try:
            # Generate embedding for the text
            embedding = self.embedding_model.encode(text)
            
            # Search across all node types
            entities = []
            for node_type, config in self.node_types.items():
                query = f"""
                MATCH (n:{'|'.join(config['labels'])})
                WHERE n.embedding IS NOT NULL AND 
                      gds.similarity.cosine(n.embedding, $embedding) > 0.7
                RETURN 
                    labels(n)[0] AS type,
                    n.name AS name,
                    id(n) AS id,
                    gds.similarity.cosine(n.embedding, $embedding) AS score
                ORDER BY score DESC
                LIMIT 3
                """
                matches = graph.query(query, params={"embedding": embedding.tolist()})
                entities.extend([dict(m) for m in matches])
            
            return entities
        
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return []

    def _search_related_entities(self, entities: list) -> list:
        """
        Find related entities based on graph relationships
        
        Args:
            entities: List of extracted entities
        
        Returns:
            List of related entities with their relationships
        """
        results = []
        for entity in entities:
            node_type = entity['type']
            config = next((v for k,v in self.node_types.items() 
                          if node_type in v['labels']), None)
            
            if config and config['relations']:
                try:
                    query = f"""
                    MATCH (n) WHERE id(n) = $id
                    MATCH (n)-[:{'|'.join(config['relations'])}]->(related)
                    RETURN 
                        labels(related)[0] AS related_type,
                        related.name AS related_name,
                        type(r) AS relationship
                    LIMIT 5
                    """
                    related = graph.query(query, params={"id": entity['id']})
                    results.append({
                        "source": entity,
                        "related": [dict(r) for r in related]
                    })
                except Exception as e:
                    logger.error(f"Related entity search failed for {entity}: {e}")
        
        return results

    def _format_response(self, results: list, query_type: str) -> str:
        """
        Enhanced response formatter with more detailed context
        
        Args:
            results: List of query results
            query_type: Type of query performed
        
        Returns:
            Formatted response string
        """
        if not results:
            return "I couldn't find matching information. Would you like me to refine the search?"
        
        if query_type == 'entity_search':
            response = ["I found these related items:"]
            for result in results:
                source = result['source']
                response.append(f"\n{source['type']} '{source['name']}' is connected to:")
                for rel in result['related']:
                    response.append(f"  - {rel['relationship']} {rel['related_type']} '{rel['related_name']}'")
            
            response.append("\nWould you like more details about any of these?")
            return "\n".join(response)
        
        # Existing fallback for other query types
        return str(results)

    def _determine_query_type(self, entities: list) -> str:
        """
        Determine the type of query based on extracted entities
        
        Args:
            entities: List of extracted entities
        
        Returns:
            Query type as a string
        """
        if not entities:
            return 'general_query'
        
        # Logic to determine query type based on entities
        entity_types = set(entity['type'] for entity in entities)
        
        if 'Symptom' in entity_types:
            return 'entity_search'
        elif 'Disease' in entity_types:
            return 'property_query'
        elif 'Treatment' in entity_types or 'Drug' in entity_types:
            return 'entity_search'
        
        return 'general_query'

    def _query_entity_properties(self, entities: list) -> list:
        """
        Query properties for specific entities
        
        Args:
            entities: List of entities to query properties for
        
        Returns:
            List of entity properties
        """
        properties = []
        for entity in entities:
            try:
                query = f"""
                MATCH (n) WHERE id(n) = $id
                RETURN properties(n) AS properties
                """
                prop_result = graph.query(query, params={"id": entity['id']})
                properties.append({
                    "entity": entity,
                    "properties": prop_result[0]['properties'] if prop_result else {}
                })
            except Exception as e:
                logger.error(f"Property query failed for {entity}: {e}")
        
        return properties

    def _general_query(self, user_question: str) -> list:
        """
        Perform a general query when no specific entities are found
        
        Args:
            user_question: User's input text
        
        Returns:
            List of general query results
        """
        try:
            # Use embedding to find semantically similar nodes
            embedding = self.embedding_model.encode(user_question)
            
            query = """
            MATCH (n)
            WHERE n.embedding IS NOT NULL AND 
                  gds.similarity.cosine(n.embedding, $embedding) > 0.6
            RETURN 
                labels(n)[0] AS type,
                n.name AS name,
                gds.similarity.cosine(n.embedding, $embedding) AS score
            ORDER BY score DESC
            LIMIT 5
            """
            
            return graph.query(query, params={"embedding": embedding.tolist()})
        
        except Exception as e:
            logger.error(f"General query failed: {e}")
            return []

    async def handle_query(self, query_data: Dict) -> Dict:
        """
        Enhanced query handling with context tracking and entity extraction
        """
        try:
            user_question = query_data.get("text", "")
            
            # Extract entities from the question
            entities = self._extract_entities(user_question)
            
            # Update session context with extracted entities
            if entities:
                self.session_context.setdefault('active_entities', []).extend(entities)
                self.session_context['query_history'].append({
                    'query': user_question,
                    'entities': entities,
                    'timestamp': datetime.now().isoformat()
                })
            
            # Determine query type based on extracted entities
            query_type = self._determine_query_type(entities)
            self.session_context['last_query_type'] = query_type
            
            # Generate and execute query based on query type
            if query_type == 'entity_search':
                results = self._search_related_entities(entities)
            elif query_type == 'property_query':
                results = self._query_entity_properties(entities)
            else:
                results = self._general_query(user_question)
            
            # Format response based on results and context
            response = self._format_response(results, query_type)
            
            return {
                "response": response,
                "context_updates": {
                    "active_entities": self.session_context['active_entities'],
                    "last_query_type": query_type,
                    "query_history": self.session_context['query_history']
                }
            }
            
        except Exception as e:
            logger.error(f"Query handling failed: {e}")
            return {
                "response": f"I encountered an error processing your query: {str(e)}",
                "context_updates": {},
                "error": str(e)
            }

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