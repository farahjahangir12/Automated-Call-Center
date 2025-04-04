import asyncio
import importlib.util
from pathlib import Path
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import logging
from datetime import datetime
import random
import re
from typing import Dict, Optional
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='hospital_router.log'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize the LLM
llm = ChatGroq(
    model_name="gemma2-9b-it",
    temperature=0.2,
    max_tokens=10,
    max_retries=1,
    timeout=2.0
)

class HospitalRouter:
    def __init__(self):
        self.routing_matrix = {
            "EMERGENCY": {
                "keywords": ["emergency", "ambulance", "urgent", "help now", "dying", "heart attack"],
                "patterns": [r"emergency|urgent|help now|heart attack"],
                "department": "HUMAN",
                "response": "🚨 Connecting to emergency services immediately!",
                "timeout": 0.1
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
                "timeout": 0.3
            },
            "MEDICAL": {
                "keywords": ["symptom", "fever", "pain", "headache", "rash", "cough", "disease", "care instructions", "treatment", "genetic linkage"],
                "patterns": [
                    r"what should I do for.*",
                    r"is.*serious",
                    r"treatment for.*",
                    r"my (child|son|daughter).*fever"
                ], 
                "department": "GRAPH",
                "response": "🩺 Analyzing your symptoms...",
                "timeout": 0.5
            },
            "GENERAL": {
                "keywords": ["admission details", "visitor guides", "department details", "payment methods", "consulting services"],
                "patterns": [r"guide|details|hours|departments|pay"],
                "department": "RAG",
                "response": "📚 Retrieving relevant information...",
                "timeout": 0.1
            },
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
            "total_time": 0.0
        }

        # Load agent modules dynamically
        self.agents = {
            "GRAPH": self._load_agent("graph"),
            "SQL": self._load_agent("sql"),
            "RAG": self._load_agent("rag")
        }
        self.verify_agents()


    def verify_agents(self):
        """Check all required agents are loaded"""
        for name, handler in self.agents.items():
            if handler is None:
                print(f"Critical: {name} agent failed to load!")
            else:
                logger.info(f"{name} agent ready")


    def _load_agent(self, agent_name: str) -> Optional[callable]:
        """Dynamically load agent module from agents directory"""
        try:
            agent_dir = Path(__file__).parent / "agents" / agent_name
            agent_path = agent_dir / "main.py"
        
            print(f"Attempting to load agent from: {agent_path}")
            if not agent_path.exists():
                print(f"Agent file not found at {agent_path}")
                return None

        # 2. Create proper module spec
            module_name = f"agents.{agent_name}.main"
            spec = importlib.util.spec_from_file_location(
            module_name,
            str(agent_path)
        )
            if spec is None:
                print(f"Couldn't create spec for {agent_name} agent")
                return None
    
        # 3. Create and execute module
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
    
        # 4. Verify required function exists
            if not hasattr(module, "handle_query"):
                print(f"{agent_name} agent missing handle_query function")
                return None
            print(f"Successfully loaded {agent_name} agent")
            return module.handle_query
        except Exception as e:
            print(f"Failed to load {agent_name} agent: {str(e)}")
            return None

    async def classify_query(self, query: str) -> tuple:
        """Classify query with detailed method tracking"""
        start_time = datetime.now()
        query_lower = query.lower()
        route_method = "LLM"

        # Check emergency first
        if any(keyword in query_lower for keyword in self.routing_matrix["EMERGENCY"]["keywords"]):
            elapsed = (datetime.now() - start_time).total_seconds()
            self.stats["fast_path"] += 1
            return "HUMAN", self.routing_matrix["EMERGENCY"]["response"], elapsed, "FAST_EMERGENCY"

        # Check other categories
        for category, config in self.routing_matrix.items():
            if category == "EMERGENCY":
                continue
                
            # Keyword check
            if any(keyword in query_lower for keyword in config["keywords"]):
                elapsed = (datetime.now() - start_time).total_seconds()
                self.stats["fast_path"] += 1
                return config["department"], config["response"], elapsed, f"FAST_{category}"
            
            # Regex check
            for pattern in self.compiled_patterns[category]:
                if pattern.search(query_lower):
                    elapsed = (datetime.now() - start_time).total_seconds()
                    self.stats["fast_path"] += 1
                    return config["department"], config["response"], elapsed, f"REGEX_{category}"

        # LLM Fallback
        try:
            prompt = f"""Classify this hospital query in ONE WORD:
            Options: [EMERGENCY, APPOINTMENT, MEDICAL, GENERAL]
            Query: "{query[:200]}"
            Classification:"""
            
            response = await asyncio.wait_for(
                llm.ainvoke([{"role": "user", "content": prompt}]),
                timeout=1.5
            )
            
            classification = response.content.strip().upper()
            elapsed = (datetime.now() - start_time).total_seconds()
            self.stats["llm_path"] += 1
            
            if classification in ["EMERGENCY", "911"]:
                return "HUMAN", self.routing_matrix["EMERGENCY"]["response"], elapsed, "LLM_EMERGENCY"
            elif classification in ["APPOINTMENT", "SCHEDULE"]:
                return "SQL", self.routing_matrix["APPOINTMENT"]["response"], elapsed, "LLM_APPOINTMENT"
            elif classification in ["MEDICAL", "SYMPTOM"]:
                return "GRAPH", self.routing_matrix["MEDICAL"]["response"], elapsed, "LLM_MEDICAL"
            elif classification in ["GENERAL", "POLICY"]:
                return "RAG", self.routing_matrix["GENERAL"]["response"], elapsed, "LLM_GENERAL"
                
        except Exception as e:
            logger.warning(f"LLM error: {str(e)[:50]}")
            elapsed = (datetime.now() - start_time).total_seconds()
        
        # Final fallback
        elapsed = (datetime.now() - start_time).total_seconds()
        return "HUMAN", "Please hold while we connect you...", elapsed, "FALLBACK"

    async def route_to_agent(self, department: str, query: str) -> str:
        """Route the query to the appropriate agent"""
        if department == "HUMAN":
            return "Please wait while we connect you to a human operator..."
        
        agent_handler = self.agents.get(department)
        if not agent_handler:
            return f"System error: {department} agent not available"
        
        try:
            response = await agent_handler(query)
            return response
        except Exception as e:
            logger.error(f"Error in {department} agent: {str(e)}")
            return f"Sorry, the {department} system is currently unavailable. Please try again later."

    async def process_query(self, query: str) -> Dict:
        """Process a single query with full diagnostics"""
        self.stats["total_queries"] += 1
        start_time = datetime.now()
        
        dept, initial_response, classify_time, method = await self.classify_query(query)
        
        # Get final response from the appropriate agent
        final_response = await self.route_to_agent(dept, query)
        
        total_time = (datetime.now() - start_time).total_seconds()
        self.stats["total_time"] += total_time
        
        return {
            "query": query,
            "department": dept,
            "initial_response": initial_response,
            "final_response": final_response,
            "processing_time": f"{total_time:.3f}s",
            "classification_method": method,
            "keywords_found": self._find_keywords(query),
            "success": True  # Assuming success after routing
        }

    def _find_keywords(self, query: str) -> str:
        """Helper to identify which keywords triggered classification"""
        query_lower = query.lower()
        found = []
        for category, config in self.routing_matrix.items():
            for keyword in config["keywords"]:
                if keyword in query_lower:
                    found.append(f"{keyword}→{category}")
        return ", ".join(found) if found else "None"

    def get_stats(self) -> Dict:
        """Current performance statistics"""
        avg_time = self.stats["total_time"] / self.stats["total_queries"] if self.stats["total_queries"] > 0 else 0
        fast_ratio = (self.stats["fast_path"] / self.stats["total_queries"]) * 100 if self.stats["total_queries"] > 0 else 0
        llm_ratio = (self.stats["llm_path"] / self.stats["total_queries"]) * 100 if self.stats["total_queries"] > 0 else 0
        
        return {
            "queries_processed": self.stats["total_queries"],
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

async def interactive_test():
    router = HospitalRouter()
    print("\n" + "="*60)
    print("🏥 Osaka University Hospital - Intelligent Routing System")
    print("="*60)
    print("Type your query or 'exit' to end the session\n")
    
    while True:
        try:
            query = input("Patient Query: ").strip()
            
            if query.lower() in ['exit', 'quit']:
                print("\nSession ended. Final statistics:")
                stats = router.get_stats()
                for k, v in stats.items():
                    print(f"{k.replace('_', ' ').title():<25}: {v}")
                break
                
            if not query:
                print("Please enter a valid query")
                continue
                
            print("\n" + "-"*60)
            print(f"Processing: '{query}'")
            
            result = await router.process_query(query)
            
            print(f"\n🔍 Classification:")
            print(f"Department: {result['department']}")
            print(f"Initial Response: {result['initial_response']}")
            print(f"Final Response: {result['final_response']}")
            print(f"Method: {result['classification_method']}")
            print(f"Keywords: {result['keywords_found']}")
            print(f"Time: {result['processing_time']}")
            
            print("\n📊 Current Stats:")
            stats = router.get_stats()
            for k, v in stats.items():
                print(f"{k.replace('_', ' ').title():<25}: {v}")
                
            print("-"*60 + "\n")
            
        except KeyboardInterrupt:
            print("\nSession interrupted. Final stats:")
            stats = router.get_stats()
            for k, v in stats.items():
                print(f"{k.replace('_', ' ').title():<25}: {v}")
            break

if __name__ == "__main__":
    asyncio.run(interactive_test())