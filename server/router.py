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
from rapidfuzz import fuzz

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
    temperature=0.1,  # Lower temperature for more consistent classification
    max_tokens=10,    # We only need a short response
    max_retries=3,
    timeout=10.0      # Faster timeout for classification
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
            await self.verify_agents()
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
                logger.error(f"Critical: {name} agent failed to load!")
            else:
                try:
                    if hasattr(handler, 'verify'):
                        # Check if verify is a coroutine function
                        if asyncio.iscoroutinefunction(handler.verify):
                            result = await handler.verify()
                        else:
                            result = handler.verify()
                            
                        if result is False:
                            logger.error(f"Critical: {name} agent verification failed!")
                        else:
                            logger.info(f"{name} agent ready")
                    else:
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
                
                # Store the agent with lowercase key
                self.agents[agent_name.lower()] = agent
                
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

    async def classify_query(self, query: str, current_department: Optional[str] = None) -> Tuple[str, float]:
        """Classify query to determine which agent should handle it using rules, fuzzy matching, and LLM reasoning"""
        try:
            # Normalize query
            query_norm = query.lower().strip()
            # If we have a current department and it's SQL, maintain it for the session
            if current_department == 'sql':
                logger.debug("Maintaining SQL session")
                return 'sql', 1.0

            # --- Improved Pattern Matching ---
            sql_patterns = [
                r"\b(book|schedule|cancel|reschedule|move|change|shift).*appointment\b",
                r"\b(register|sign up|enroll|add).*patient\b",
                r"\bdoctor\b.*\b(available|schedule|time|slot|book|see)\b",
                r"\bappointment with (dr\.|doctor)\b",
                r"\bsee (dr\.|doctor)\b",
                r"\b\d{1,2}[:.]\d{2}\b",  # Time format HH:MM or HH.MM
                r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|today|tomorrow)\b",
                r"\bclinic hours\b",
                r"\bconsultation (slot|time|hours)\b"
            ]
            graph_patterns = [
                r"\b(symptom|pain|fever|diagnosis|treatment|disease|condition|allergy|asthma|diabetes|hypertension|migraine|cough|rash|headache)\b",
                r"\bwhat should i do for\b",
                r"\bis.*serious\b",
                r"\btreatment for\b",
                r"\bmy (child|son|daughter).*fever\b",
                r"\bsymptoms of\b",
                r"\bcauses of\b",
                r"\bprevention of\b",
                r"\brisks of\b",
                r"\bcomplications of\b",
                r"\bhow to treat\b",
                r"\bhow to prevent\b",
                r"\bwhat causes\b",
                r"\bwhat are the symptoms of\b",
                r"\bhow to manage\b",
                r"\bwhat is.*disease\b",
                r"\bhow to diagnose\b",
                r"\bwhat are the risk factors for\b"
            ]
            rag_patterns = [
                r"\b(policy|insurance|visiting hours|consulting hours|rules|procedure|admission|department details|payment methods|payment options|payment details|hospital info|general info|contact|location|address|parking|facilities)\b"
            ]

            def fuzzy_match(patterns, query):
                for pattern in patterns:
                    if re.search(pattern, query):
                        return True
                    # Fuzzy match for each word in pattern
                    for word in re.findall(r'\\w+', pattern):
                        if fuzz.partial_ratio(word, query) > 85:
                            return True
                return False

            # 1. Direct pattern or fuzzy match
            if fuzzy_match(sql_patterns, query_norm):
                logger.debug("Query matched SQL pattern or fuzzy")
                return "sql", 0.9
            if fuzzy_match(graph_patterns, query_norm):
                logger.debug("Query matched GRAPH pattern or fuzzy")
                return "graph", 0.9
            if fuzzy_match(rag_patterns, query_norm):
                logger.debug("Query matched RAG pattern or fuzzy")
                return "rag", 0.9

            # 2. Use context (if available)
            # Example: If last agent was SQL and query is ambiguous, prefer SQL
            # (Optional: can be expanded with ConversationContext)

            # 3. Fallback to LLM (with improved prompt)
            try:
                response = await self.llm.invoke([
                    {"role": "system", "content": """You are a query classifier for a hospital system.\nClassify queries as either:\n- sql: For appointments, registrations, and scheduling\n- graph: For medical queries, symptoms, and diagnosis\n- rag: For general hospital information, policies, and rules\nRespond ONLY with: classification|confidence_score\nExample: sql|0.9"""},
                    {"role": "user", "content": query}
                ])
                result = response.choices[0].message.content.strip()
                classification, confidence = result.split('|')
                confidence = float(confidence)
                return classification.lower().strip(), confidence
            except Exception as e:
                logger.error(f"Error in LLM classification: {str(e)}")
                # Default to RAG with lower confidence if LLM fails
                return "rag", 0.7
        except Exception as e:
            logger.error(f"Error in query classification: {str(e)}")
            return "rag", 0.5

    def _is_follow_up(self, query: str, current_department: str) -> bool:
        """Determine if query is a follow-up to current session"""
        follow_up_keywords = {
            "SQL": ["yes", "no", "confirm", "cancel", "reschedule", "book", "appointment"],
            "GRAPH": ["symptom", "pain", "treatment", "diagnosis", "result"],
            "RAG": ["more about", "explain", "details", "information", "policy"]
        }
        
        query_lower = query.lower()
        keywords = follow_up_keywords.get(current_department, [])
        return any(keyword in query_lower for keyword in keywords)

    async def route_to_agent(self, department: str, query: str, session_id: Optional[str] = None, maintain_context: bool = False) -> Dict:
        """Route the query to the appropriate agent with session context"""
        logger.info(f"Routing query to {department} agent: {query}")
        logger.debug(f"Session ID: {session_id}")
        
        if department == "human":
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
            # Only reset context if not maintaining context from active session
            if not maintain_context and session_id not in self.active_sessions:
                self.context_manager.clear_context()
            
            # For active sessions, we want to maintain the context
            if maintain_context:
                logger.debug(f"Maintaining context for active session: {session_id}")
                
            # Get fresh context for agent
            logger.debug(f"Getting context for agent: {department}")
            context = {
                "session_id": session_id or self._generate_session_id(query),
                "department": department.lower(),
                "timestamp": datetime.now().isoformat(),
                "is_new_session": session_id not in self.active_sessions
            }
            
            # Create query data
            query_data = {
                "text": query,
                "context": context
            }
            
            # Call agent handler
            logger.info(f"Calling {department} agent handler")
            logger.debug(f"Query data: {query_data}")
            
            # Get agent instance
            agent = agent_handler
            
            if not agent:
                return {
                    "response": f"Error: No handler found for {department}",
                    "context_updates": {},
                    "suggested_next": "HUMAN"
                }
                
            try:
                # Call agent's handle_query method and await the response
                response = await agent.handle_query(query_data)
                
                # Ensure response is a dictionary
                if not isinstance(response, dict):
                    response = {
                        "response": str(response) if response else "No response from agent",
                        "context_updates": {},
                        "suggested_next": None
                    }
                
                # Log response
                logger.info(f"Received response from {department} agent")
                logger.debug(f"Agent response: {response}")
                
                return response
                
            except Exception as e:
                logger.error(f"Error in {department} agent: {str(e)}")
                return {
                    "response": f"Error in {department} agent: {str(e)}",
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
        Process a query with session support and ensure resolution.
        If status is active, maintains the same agent for continuity.
        """
        try:
            # Clean up old sessions
            self._cleanup_sessions()
            
            # Get or create session ID
            if not session_id:
                # Check for any active SQL sessions that are still in progress
                active_sql_sessions = {
                    sid: session for sid, session in self.active_sessions.items()
                    if session.get('department') == 'sql' and session.get('status') == 'in_progress'
                }
                
                if active_sql_sessions:
                    # Use the most recent active SQL session
                    session_id = max(active_sql_sessions.keys(), key=lambda x: active_sql_sessions[x]['last_activity'])
                    logger.debug(f"Using existing SQL session: {session_id}")
                else:
                    session_id = self._generate_session_id(query)
                    logger.debug(f"Created new session: {session_id}")
            
            # Get current department from active session if it exists
            current_department = None
            if session_id in self.active_sessions:
                current_department = self.active_sessions[session_id].get('department')
                current_status = self.active_sessions[session_id].get('status')
                
                # If we have an active SQL session in progress, maintain it
                if current_department == 'sql' and current_status == 'in_progress':
                    department = 'sql'
                    confidence = 1.0
                    logger.debug(f"Maintaining active SQL session: {session_id}")
                else:
                    # Classify query with current department context
                    logger.debug(f"Classifying query: {query}")
                    department, confidence = await self.classify_query(query, current_department)
            else:
                # New session, classify the query
                logger.debug(f"Classifying query: {query}")
                department, confidence = await self.classify_query(query, None)
            
            logger.info(f"Query classified as {department} with confidence {confidence}")
            
            # Route to agent
            result = await self.route_to_agent(department, query, session_id)
            
            # Ensure result is properly formatted
            if asyncio.iscoroutine(result):
                result = await result
                
            if isinstance(result, dict):
                # Update session activity and department
                if session_id not in self.active_sessions:
                    self.active_sessions[session_id] = {}
                
                # Get the status from the result, defaulting to 'in_progress' for SQL department
                status = result.get('status')
                if department == 'sql' and not status:
                    status = 'in_progress'
                
                self.active_sessions[session_id].update({
                    "last_activity": datetime.now(),
                    "department": department,
                    "status": status
                })
                
                # Only clear context if query is explicitly resolved
                if status == 'resolved':
                    self.context_manager.clear_context()
                    
                return result
            else:
                # Handle case where result is not a dictionary
                response = {
                    "response": str(result) if result else "No response from agent",
                    "context_updates": {},
                    "suggested_next": None,
                    "status": "resolved"
                }
                self.context_manager.clear_context()
                return response
                
        except Exception as e:
            import traceback
            logger.error(f"Error processing query: {str(e)}")
            logger.error(traceback.format_exc())
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
                try:
                    result = await router.process_query(query)
                    if asyncio.iscoroutine(result):
                        result = await result
                        
                    if result and 'response' in result:
                        print(f"Agent: {result['response']}")
                except Exception as e:
                    print(f"Error: {str(e)}")
                
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