import asyncio
import importlib.util
import traceback
from pathlib import Path
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta
import random
import re
from typing import Dict, Optional, Tuple, Any
import sys
import hashlib
import json

# Add the server directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))
from context import ContextManager

# Configure logging
# Create handlers for both file and console output
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG level

# Create file handler
file_handler = logging.FileHandler('hospital_router.log')
file_handler.setLevel(logging.DEBUG)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

load_dotenv()

# Initialize the LLM
llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0.2,
    max_tokens=1000,
    max_retries=3,
    timeout=30.0
)

class HospitalRouter:
    def __init__(self):
        # Initialize context manager
        self.context_manager = ContextManager()
        
        self.routing_matrix = {
            "EMERGENCY": {
                "keywords": ["emergency", "ambulance", "urgent", "help now", "dying", "heart attack"],
                "patterns": [r"emergency|urgent|help now|heart attack"],
                "department": "SQL",
                "response": "🚨 Connecting to emergency services immediately!",
                "timeout": 0.1,
                "priority": 100
            },
            "APPOINTMENT": {
                "keywords": ["appointment", "schedule", "book", "reschedule", "cancel", "doctor", "dr."],
                "patterns": [
                    r"(book|schedule|reschedule|cancel).*appointment",
                    r"appointment with (dr\.|doctor)",
                    r"see (dr\.|doctor).*"
                ],
                "department": "SQL",
                "response": "📅 Connecting you to appointment services...",
                "timeout": 0.3,
                "priority": 80
            },
            "MEDICAL": {
                "keywords": ["symptom", "fever", "pain", "headache", "rash", "cough", "disease", "care instructions", "treatment", "genetic linkage", "migraine", "diabetes", "hypertension", "asthma", "allergy"],
                "patterns": [
                    r"what should I do for.*",
                    r"is.*serious",
                    r"treatment for.*",
                    r"my (child|son|daughter).*fever",
                    r"symptoms of.*",
                    r"causes of.*",
                    r"treatment for.*",
                    r"prevention of.*",
                    r"risks of.*",
                    r"complications of.*",
                    r"how to treat.*",
                    r"how to prevent.*",
                    r"what causes.*",
                    r"what are the symptoms of.*",
                    r"how to manage.*",
                    r"what is.*disease",
                    r"what is.*condition",
                    r"how to diagnose.*",
                    r"what are the risk factors for.*"
                ],
                "department": "GRAPH",
                "response": "🩺 Analyzing your symptoms and medical information...",
                "timeout": 0.5,
                "priority": 90
            },
            "GENERAL": {
                "keywords": [
                    "consulting hours", "visiting hours", "admission policy", "admission details", 
                    "department details", "payment methods", "payment options", "payment details",
                    "consulting services", "visiting hours", "ward",
                    "wards", "admission", "discharge", "visitor guide", "visitor policy",
                    "cash", "credit card", "debit", "insurance", "payment"
                ],
                "patterns": [
                    r"consulting.*hours",
                    r"visiting.*hours",
                    r"admission.*policy",
                    r"admission.*details",
                    r"department.*details",
                    r"payment.*methods",
                    r"payment.*options",
                    r"payment.*details",
                    r"consulting.*services",
                    r"visiting.*hours",
                    r"ward.*hours",
                    r"admission.*",
                    r"discharge.*",
                    r"visitor.*guide",
                    r"visitor.*policy",
                    r"cash.*payment",
                    r"credit.*card.*payment",
                    r"debit.*payment",
                    r"insurance.*payment",
                    r"payment.*options",
                    r"payment.*methods"
                ],
                "department": "RAG",
                "response": "📚 Retrieving relevant information...",
                "timeout": 0.1,
                "priority": 70
            }
        }

        # Pre-compile regex patterns for speed
        self.compiled_patterns = {}
        for category, config in self.routing_matrix.items():
            self.compiled_patterns[category] = [
                re.compile(pattern, re.IGNORECASE) 
                for pattern in config.get("patterns", [])
            ]

        self.stats = {
            "total_queries": 0,
            "fast_path": 0,
            "llm_path": 0,
            "total_time": 0.0,
            "sessions_created": 0,
            "session_continuations": 0
        }

        # Initialize empty agents dict
        self.agents = {}
        
        # Session management
        self.active_sessions = {}
        self.session_timeout = timedelta(minutes=15)  # 15 minute session timeout
        
        # Initialization flag
        self._initialized = False
    
    @classmethod
    async def create(cls) -> 'HospitalRouter':
        """Factory method to create and initialize a HospitalRouter instance"""
        self = cls()
        await self.initialize()
        return self
    
    async def initialize(self) -> None:
        if self._initialized:
            return

        logger.info("Starting agent initialization...")
        logger.debug("Environment variables verified")
        
        agent_names = ["sql", "rag", "graph"]
        logger.debug(f"Loading agents: {agent_names}")
        
        try:
            results = await asyncio.gather(*[
                self._load_agent(name) for name in agent_names
            ])
            logger.debug(f"Agent loading results: {results}")

            if not all(results):
                failed = [name for name, success in zip(agent_names, results) if not success]
                logger.error(f"Failed to load agents: {failed}")
                logger.error("Agent loading failure details:")
                for agent in failed:
                    logger.error(f"{agent} loading traceback:")
                    logger.error(traceback.format_exc())
                raise RuntimeError(f"Failed to load agents: {failed}")

            logger.debug("Verifying agent interfaces...")
            self.verify_agents()
            logger.debug("Agent verification complete")
            
            self._initialized = True
            logger.info("All agents initialized successfully")
        except Exception as e:
            logger.error(f"Critical initialization failure: {str(e)}")
            logger.error("Full initialization traceback:")
            logger.error(traceback.format_exc())
            raise

    async def verify_agents(self):
        """Check all required agents are loaded"""
        for name, handler in self.agents.items():
            if handler is None:
                print(f"Critical: {name} agent failed to load!")
            else:
                try:
                    if hasattr(handler, 'verify'):
                        await handler.verify()
                    logger.info(f"{name} agent ready")
                except Exception as e:
                    logger.error(f"Error verifying {name} agent: {str(e)}")

    async def _load_agent(self, agent_name: str):
        try:
            print(f"DEBUG: Starting to load {agent_name} agent")
            # Use absolute path to find agent modules
            agent_path = Path(__file__).parent / "agents" / agent_name / "__init__.py"
            print(f"DEBUG: Looking for agent module at {agent_path}")
            
            if not agent_path.exists():
                print(f"ERROR: Agent module not found at {agent_path}")
                return False
            print(f"DEBUG: Found agent module at {agent_path}")

            print(f"DEBUG: Creating spec for {agent_name} agent")
            spec = importlib.util.spec_from_file_location(f"agents.{agent_name}", agent_path)
            if not spec or not spec.loader:
                print(f"ERROR: Failed to load spec for {agent_name} agent")
                return False
            print(f"DEBUG: Created spec for {agent_name} agent")

            print(f"DEBUG: Creating module from spec for {agent_name} agent")
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"agents.{agent_name}"] = module
            
            print(f"DEBUG: Executing module for {agent_name} agent")
            try:
                spec.loader.exec_module(module)
                print(f"DEBUG: Successfully executed module for {agent_name} agent")
            except Exception as module_error:
                print(f"ERROR: Error executing module for {agent_name} agent: {str(module_error)}")
                print(traceback.format_exc())
                return False

            # Check if get_agent function exists
            if not hasattr(module, 'get_agent'):
                print(f"ERROR: No get_agent function found in {agent_name} module")
                return False
            print(f"DEBUG: Found get_agent function in {agent_name} module")

            # Get agent instance using the factory method
            print(f"DEBUG: Getting agent instance for {agent_name} agent")
            try:
                agent = await module.get_agent()
                print(f"DEBUG: Got agent instance for {agent_name} agent")
                
                # Store the agent with proper case
                self.agents[agent_name.upper()] = agent
                
                # Only call initialize if it exists and is callable AND agent_name is not 'rag' or 'graph'
                if agent_name.lower() not in ['rag', 'graph'] and hasattr(agent, 'initialize') and callable(getattr(agent, 'initialize')):
                    print(f"DEBUG: Initializing {agent_name} agent")
                    try:
                        await agent.initialize()
                        print(f"DEBUG: Initialized {agent_name} agent")
                    except Exception as init_error:
                        print(f"ERROR: Error initializing {agent_name} agent: {str(init_error)}")
                        print(traceback.format_exc())
                        return False
                
                print(f"INFO: Successfully loaded {agent_name} agent")
                return True
            except Exception as agent_error:
                print(f"ERROR: Error getting agent instance for {agent_name} agent: {str(agent_error)}")
                print(traceback.format_exc())
                return False
            
        except Exception as e:
            print(f"ERROR: Failed to load {agent_name} agent: {str(e)}")
            print(f"ERROR: Agent error traceback: {traceback.format_exc()}")
            return False

    async def classify_query(self, query: str, current_department: Optional[str] = None) -> Tuple[str, str, float, str]:
        """Classify query with context awareness"""
        start_time = datetime.now()
        
        # Get context from context manager
        context = self.context_manager.get_context("sql") if current_department == "SQL" else {}
        
        # Determine if this is a follow-up query
        is_follow_up = self._is_follow_up(query, current_department)
        
        # If it's a follow-up, prioritize current department
        if is_follow_up and current_department:
            department = current_department
            response = "Continuing previous conversation..."
            route_type = "follow_up"
            return department, response, (datetime.now() - start_time).total_seconds(), route_type
        
        # Check for emergency keywords first
        for category, config in self.routing_matrix.items():
            if any(keyword in query.lower() for keyword in config["keywords"]):
                for pattern in self.compiled_patterns[category]:
                    if pattern.search(query):
                        department = config["department"]
                        response = config["response"]
                        route_type = "keyword_match"
                        return department, response, (datetime.now() - start_time).total_seconds(), route_type
        
        # If no keyword match, use LLM for classification
        llm = ChatGroq(
            model_name="llama-3.3-70b-versatile",
            temperature=0.2,
            max_tokens=1000,
            max_retries=3,
            timeout=30.0
        )
        
        # Enhanced prompt with more specific instructions
        prompt = """You are a hospital query router. Your task is to classify the following query and determine the most appropriate department to handle it.

Query: {query}

Current Context: {context}

Classify this query into one of these categories:
- EMERGENCY: Immediate medical emergencies
- APPOINTMENT: Scheduling and appointments
- MEDICAL: Medical symptoms and treatment questions
- GENERAL: General hospital information (including payment methods, visiting hours, admission policies)

For each category, consider:
1. Emergency: Look for words like "emergency", "ambulance", "urgent", "help now"
2. Appointment: Look for words like "appointment", "schedule", "book", "doctor"
3. Medical: Look for medical symptoms or treatment questions
4. General: Look for general information requests about hospital facilities, payment options, visiting hours, admission policies

Respond with JSON in this format:
{{
    "department": "DEPARTMENT_NAME",
    "reason": "Brief explanation of why this department was chosen",
    "confidence": "high|medium|low"
}}
"""
        
        try:
            # Use ainvoke instead of __call__
            response = await llm.ainvoke(prompt.format(query=query, context=context))
            result = json.loads(response.content)
            
            department = result["department"]
            response = f"Routing to {department} department... ({result['reason']})"
            route_type = "llm_classification"
            
            # Update context with routing decision
            self.context_manager.update_context("sql", {
                "last_routing": {
                    "department": department,
                    "reason": result["reason"],
                    "confidence": result["confidence"]
                }
            })
            
            return department, response, (datetime.now() - start_time).total_seconds(), route_type
            
        except Exception as e:
            logger.error(f"Error in query classification: {str(e)}")
            # Default to RAG only if it's not a medical query
            if any(keyword in query.lower() for keyword in self.routing_matrix["MEDICAL"]["keywords"]):
                department = "GRAPH"
                response = "Unable to classify query. Routing to medical department."
            else:
                department = "RAG"
                response = "Unable to classify query. Routing to information department."
            route_type = "error"
            return department, response, (datetime.now() - start_time).total_seconds(), route_type

    def _is_follow_up(self, query: str, current_department: str) -> bool:
        """Determine if query is a follow-up to current session"""
        follow_up_keywords = {
            "SQL": ["about my", "appointment", "change", "cancel", "reschedule"],
            "GRAPH": ["symptom", "pain", "treatment", "diagnosis", "result"],
            "RAG": ["more about", "explain", "details", "information", "policy"]
        }
        
        query_lower = query.lower()
        keywords = follow_up_keywords.get(current_department, [])
        return any(keyword in query_lower for keyword in keywords)

    async def route_to_agent(self, department: str, query: str, session_id: Optional[str] = None) -> Dict:
        """Route the query to the appropriate agent with session context"""
        logger.info(f"Routing query to {department} agent: {query}")
        logger.debug(f"Session ID: {session_id}")
        
        if department == "HUMAN":
            return {
                "response": "Please wait while we connect you to a human operator...",
                "context_updates": {},
                "suggested_next": None
            }
        
        agent_handler = self.agents.get(department)
        if not agent_handler:
            logger.error(f"Agent handler not found for department: {department}")
            return {
                "response": f"System error: {department} agent not available",
                "context_updates": {},
                "suggested_next": "HUMAN"
            }
        
        try:
            # Get agent-specific context
            agent_id = department.lower()
            logger.debug(f"Getting context for agent: {agent_id}")
            agent_context = self.context_manager.get_context(agent_id)
            
            # Merge with session context
            context = {
                "session_id": session_id,
                "department": department,
                "timestamp": datetime.now().isoformat(),
                **agent_context  # Include agent-specific context
            }
            
            if session_id and session_id in self.active_sessions:
                session_context = self.active_sessions[session_id].get("context", {})
                logger.debug(f"Adding session context: {session_context}")
                context.update(session_context)
            
            # Pass query and merged context to agent
            logger.info(f"Calling {department} agent handler")
            query_data = {
                "text": query,
                "context": context
            }
            logger.debug(f"Query data: {query_data}")
            
            try:
                response = await agent_handler.handle_query(query_data)
                
                # If the agent returned a coroutine, await it
                if asyncio.iscoroutine(response):
                    response = await response
                
                logger.info(f"Received response from {department} agent")
                logger.debug(f"Agent response: {response}")
                
                if not isinstance(response, dict):
                    logger.warning(f"Invalid response format from {department} agent")
                    return {
                        "response": str(response),
                        "context_updates": {},
                        "suggested_next": None
                    }
                return response
            except Exception as agent_error:
                logger.error(f"Error from {department} agent handler: {str(agent_error)}")
                logger.error(f"Agent error traceback: {traceback.format_exc()}")
                return {
                    "response": f"Sorry, the {department} system encountered an error. Please try again.",
                    "context_updates": {},
                    "suggested_next": "HUMAN"
                }
            
        except Exception as e:
            logger.error(f"Error in route_to_agent: {str(e)}")
            logger.error(f"Route error traceback: {traceback.format_exc()}")
            return {
                "response": f"Sorry, the {department} system is currently unavailable. Please try again later.",
                "context_updates": {},
                "suggested_next": "HUMAN"
            }

    async def process_query(self, query: str, session_id: Optional[str] = None) -> Dict:
        """
        Process a query with session support
        """
        try:
            # Clean up old sessions and context
            self._cleanup_sessions()
            self.stats["total_queries"] += 1
            start_time = datetime.now()
            
            # Get current department if session exists
            current_department = None
            if session_id and session_id in self.active_sessions:
                current_department = self.active_sessions[session_id]["department"]
            
            # Classify query with context awareness
            department, response, classification_time, route_type = await self.classify_query(query, current_department)
            
            # Print routing information
            print(f"\n=== Query Routing Information ===")
            print(f"Query: {query}")
            print(f"Route Type: {route_type}")
            print(f"Department: {department}")
            print(f"Routing Response: {response}")
            print(f"Classification Time: {classification_time:.3f}s")
            print("-" * 80)
            
            # Get the appropriate agent
            agent = self.agents.get(department)
            if not agent:
                print(f"Warning: No agent found for department '{department}'")
                return {
                    "response": f"No agent available for department '{department}'",
                    "context_updates": {},
                    "suggested_next": None
                }
            
            # Process the query with the agent
            query_data = {
                "text": query,
                "context": self.active_sessions[session_id]["context"] if session_id and session_id in self.active_sessions else {},
                "history": self.active_sessions[session_id]["history"] if session_id and session_id in self.active_sessions else []
            }
            
            # Print agent processing information
            print(f"\n=== Agent Processing Information ===")
            print(f"Agent: {department}")
            print(f"Query: {query}")
            print("-" * 80)
            
            result = await agent.handle_query(query_data)
            
            # Update session context with agent's context updates
            if session_id and session_id in self.active_sessions:
                self.active_sessions[session_id]["context"].update(result.get("context_updates", {}))
            
            return result
            
        except Exception as e:
            import traceback
            print(f"Error processing query: {str(e)}")
            traceback.print_exc()
            return {
                "response": f"Error processing query: {str(e)}",
                "context_updates": {},
                "suggested_next": None
            }

    def _cleanup_sessions(self):
        """Remove inactive sessions and their context"""
        now = datetime.now()
        inactive_threshold = timedelta(minutes=5)
        
        for session_id, session in list(self.active_sessions.items()):
            if (now - session["last_activity"]) > inactive_threshold:
                del self.active_sessions[session_id]

    def _generate_session_id(self, query: str) -> str:
        """Generate a unique session ID based on query and timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
        return f"sess_{timestamp}_{query_hash}"

    def get_stats(self) -> Dict:
        """Current performance statistics"""
        avg_time = self.stats["total_time"] / self.stats["total_queries"] if self.stats["total_queries"] > 0 else 0
        fast_ratio = (self.stats["fast_path"] / self.stats["total_queries"]) * 100 if self.stats["total_queries"] > 0 else 0
        llm_ratio = (self.stats["llm_path"] / self.stats["total_queries"]) * 100 if self.stats["total_queries"] > 0 else 0
        session_ratio = (self.stats["session_continuations"] / self.stats["total_queries"]) * 100 if self.stats["total_queries"] > 0 else 0
        
        return {
            "queries_processed": self.stats["total_queries"],
            "sessions_created": self.stats["sessions_created"],
            "session_continuations": self.stats["session_continuations"],
            "session_continuation_rate": f"{session_ratio:.1f}%",
            "avg_response_time": f"{avg_time:.3f}s",
            "fast_path_percentage": f"{fast_ratio:.1f}%",
            "llm_fallback_percentage": f"{llm_ratio:.1f}%",
            "performance_grade": self._calculate_grade(avg_time, fast_ratio)
        }

    def _calculate_grade(self, avg_time: float, fast_ratio: float) -> str:
        """Calculate a simple performance grade"""
        if avg_time < 0.2 and fast_ratio > 80:
            return "A+ (Optimal)"
        elif avg_time < 0.3 and fast_ratio > 70:
            return "A (Excellent)"
        elif avg_time < 0.5 and fast_ratio > 50:
            return "B (Good)"
        elif avg_time < 1.0:
            return "C (Acceptable)"
        return "D (Needs Improvement)"

# Main function to run the router with interactive input
async def main():
    """Main function to run the router with interactive input"""
    try:
        # Create and initialize router
        router = await HospitalRouter.create()
        print("Router initialized")
        print("Type 'quit' to exit")
        print("Enter your query:")

        while True:
            try:
                # Get user input
                query = input("You: ").strip()
                
                if query.lower() == 'quit':
                    break
                    
                if not query:
                    continue

                # Process the query
                result = await router.process_query(query)
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {str(e)}")
                continue

        # Clean up sessions before exiting
        router._cleanup_sessions()

    except Exception as e:
        print(f"Critical error: {str(e)}")
        logger.error(f"Critical error: {str(e)}")
        logger.error(traceback.format_exc())

    finally:
        # Clean up sessions if router exists
        if 'router' in locals():
            router._cleanup_sessions()

if __name__ == "__main__":
    asyncio.run(main())