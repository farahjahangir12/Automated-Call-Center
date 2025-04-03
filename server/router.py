import asyncio
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import logging
from datetime import datetime
import random
import re
from typing import Tuple, Dict

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
    model_name="mixtral-8x7b-32768",
    temperature=0.2,
    max_tokens=10,
    max_retries=1,
    timeout=2.0
)

class InteractiveRouter:
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
                "keywords": ["symptom", "fever", "pain", "headache", "rash", "cough","disease","care instructions","treatment","genetic linkage"],
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
            "General Polcies": {
                "keywords": ["admisssion details", "visitor guides", "department details", "payment methods", "consulting services"],
                "patterns": [r"guide|details|hours|departments|pay"],
                "department": "RAG",
                "response": "🚨 Connecting to RAG Agent!",
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

    async def classify_query(self, query: str) -> Tuple[str, str, float, str]:
        """Classify with detailed method tracking"""
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
                return category, config["response"], elapsed, f"FAST_{category}"
            
            # Regex check
            for pattern in self.compiled_patterns[category]:
                if pattern.search(query_lower):
                    elapsed = (datetime.now() - start_time).total_seconds()
                    self.stats["fast_path"] += 1
                    return category, config["response"], elapsed, f"REGEX_{category}"

        # LLM Fallback
        try:
            prompt = f"""Classify this hospital query in ONE WORD:
            Options: [EMERGENCY, APPOINTMENT, MEDICAL, OTHER]
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
                
        except Exception as e:
            logger.warning(f"LLM error: {str(e)[:50]}")
            elapsed = (datetime.now() - start_time).total_seconds()
        
        # Final fallback
        elapsed = (datetime.now() - start_time).total_seconds()
        return "HUMAN", "Please hold while we connect you...", elapsed, "FALLBACK"

    async def process_query(self, query: str) -> Dict:
        """Process a single query with full diagnostics"""
        self.stats["total_queries"] += 1
        start_time = datetime.now()
        
        dept, response, classify_time, method = await self.classify_query(query)
        processing_time = self.routing_matrix.get(dept, {}).get("timeout", 0.5)
        
        await asyncio.sleep(min(processing_time, 1.0))
        
        total_time = (datetime.now() - start_time).total_seconds()
        self.stats["total_time"] += total_time
        
        return {
            "query": query,
            "department": dept,
            "response": response,
            "processing_time": f"{total_time:.3f}s",
            "classification_method": method,
            "keywords_found": self._find_keywords(query),
            "success": random.random() > 0.05
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
    router = InteractiveRouter()
    print("\n" + "="*60)
    print("🏥 Osaka University Hospital - Interactive Routing System")
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
            print(f"Response: {result['response']}")
            print(f"Method: {result['classification_method']}")
            print(f"Keywords: {result['keywords_found']}")
            print(f"Time: {result['processing_time']}")
            print(f"Success: {'✅' if result['success'] else '❌ (Retrying...)'}")
            
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