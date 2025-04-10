import asyncio
import logging
from typing import Dict, Any
import sys
import os

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from router import Router
from agents.rag.main import HospitalRAGSystem
from agents.graph.main import MedicalGraphSystem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestRouterEscalation:
    def __init__(self):
        self.router = Router()
        self.test_data = {
            "rag_queries": [
                "What are the visiting hours for outpatients?",
                "How do I pay my hospital bills?",
                "What's the process for getting a medical certificate?"
            ],
            "graph_queries": [
                "What departments are available?",
                "Show me the patient care process.",
                "What are the emergency procedures?"
            ],
            "escalation_scenarios": [
                {
                    "query": "I need help with my medical records.",
                    "expected_department": "RAG",
                    "follow_up": "Can you show me the process flow?",
                    "expected_department_follow_up": "GRAPH"
                },
                {
                    "query": "Tell me about the hospital's emergency services.",
                    "expected_department": "GRAPH",
                    "follow_up": "What's the billing process for emergency services?",
                    "expected_department_follow_up": "RAG"
                }
            ]
        }

    async def test_query_escalation(self):
        """Test query escalation between RAG and Graph agents"""
        print("\n=== Starting Router Escalation Test ===\n")
        
        # Test RAG queries
        print("\n=== Testing RAG Queries ===\n")
        for query in self.test_data["rag_queries"]:
            print(f"\nQuery: {query}")
            result = await self.router.process_query({"text": query})
            print(f"Response: {result['response']}")
            print(f"Department: {result['department']}")

        # Test Graph queries
        print("\n=== Testing Graph Queries ===\n")
        for query in self.test_data["graph_queries"]:
            print(f"\nQuery: {query}")
            result = await self.router.process_query({"text": query})
            print(f"Response: {result['response']}")
            print(f"Department: {result['department']}")

        # Test escalation scenarios
        print("\n=== Testing Escalation Scenarios ===\n")
        for scenario in self.test_data["escalation_scenarios"]:
            print(f"\nScenario: {scenario['query']}")
            
            # Initial query
            print("\nInitial Query:")
            result = await self.router.process_query({"text": scenario['query']})
            print(f"Response: {result['response']}")
            print(f"Department: {result['department']}")
            
            # Follow-up query
            print("\nFollow-up Query:")
            result = await self.router.process_query({
                "text": scenario['follow_up'],
                "context": result.get("context", {})
            })
            print(f"Response: {result['response']}")
            print(f"Department: {result['department']}")

if __name__ == "__main__":
    test = TestRouterEscalation()
    asyncio.run(test.test_query_escalation())
