"""
Agent Handoff Protocol Implementation

This module implements a robust handoff protocol for transitioning between
specialized agents (SQL, RAG, Graph) in the automated call center system.
"""

import logging
import re
from typing import Dict, List, Tuple, Any, Optional
from conversation_context import ConversationContext

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class HandoffValidator:
    """Validates handoff decisions to prevent loops and ensure appropriate transitions"""
    
    @staticmethod
    def validate_handoff(source_agent: str, target_agent: str, context: ConversationContext) -> Tuple[bool, str]:
        """
        Ensure handoff is appropriate and wouldn't create loops
        
        Args:
            source_agent: Current agent
            target_agent: Proposed agent to hand off to
            context: Conversation context
            
        Returns:
            Tuple[bool, str]: (is_valid, reason)
        """
        # Check if this would create a loop 
        # (e.g., SQL → Graph → SQL → Graph within 4 turns)
        if context.handoff_count >= 3:
            recent_agents = context.previous_agents[-3:]
            if source_agent in recent_agents and target_agent in recent_agents:
                return False, "Would create a handoff loop"
                
        # Don't allow immediate bounce-back to previous agent
        if context.previous_agents and context.previous_agents[-1] == target_agent:
            return False, "Would immediately return to previous agent"
            
        # Check agent compatibility with entities
        # If we have medical entities, prefer GRAPH agent
        if "symptom" in context.entities and target_agent != "graph":
            confidence = sum([e["confidence"] for e in context.entities.get("symptom", [])])
            if confidence > 1.5:  # Multiple symptoms or high confidence
                return False, "Medical entities detected, should use Graph agent"
                
        # If we have appointment entities, prefer SQL agent
        if any(k in context.entities for k in ["date", "time", "doctor"]) and target_agent != "sql":
            return False, "Appointment entities detected, should use SQL agent"
            
        return True, "Handoff is valid"

class HandoffMatrix:
    """Defines which agents can hand off to whom and handles matrix configuration"""
    
    def __init__(self):
        # Default handoff matrix - which agents can hand off to which others
        self.matrix = {
            "sql": ["graph", "rag"],
            "rag": ["sql", "graph"],
            "graph": ["sql", "rag"]
        }
        
        # Handoff transition messages to users
        self.transitions = {
            ("sql", "graph"): "I'll connect you with our medical specialist to discuss those symptoms.",
            ("rag", "sql"): "Let me transfer you to our scheduling expert to help with that appointment.",
            ("graph", "rag"): "I'll have our policy specialist answer your question about hospital procedures.",
            ("sql", "rag"): "Let me transfer you to our hospital information specialist for that policy question.",
            ("graph", "sql"): "I'll connect you with our scheduling system to help with that appointment request.",
            ("rag", "graph"): "Let me transfer you to our medical specialist who can better answer your health question."
        }
        
    def can_handoff(self, source: str, target: str) -> bool:
        """Check if source agent can hand off to target agent"""
        return source in self.matrix and target in self.matrix[source]
        
    def get_transition_message(self, source: str, target: str) -> str:
        """Get appropriate transition message for this handoff"""
        key = (source, target)
        return self.transitions.get(key, "Let me connect you with a specialist who can better help with your question.")
        
    def get_valid_targets(self, source: str) -> List[str]:
        """Get list of valid handoff targets for this source agent"""
        return self.matrix.get(source, [])
        
    def update_matrix(self, new_rules: Dict[str, List[str]]) -> None:
        """Update handoff rules based on analytics or configuration"""
        self.matrix.update(new_rules)

class HandoffProtocol:
    """Main class implementing the agent handoff protocol"""
    
    def __init__(self):
        self.matrix = HandoffMatrix()
        self.validator = HandoffValidator()
        
    def check_handoff_needed(self, agent: str, query: str, 
                             response: Dict[Any, Any], context: ConversationContext) -> Tuple[bool, str, float]:
        """
        Determine if a handoff is needed based on multiple criteria
        
        Args:
            agent: Current agent handling the conversation
            query: User's query
            response: The agent's response data including confidence
            context: Conversation context
            
        Returns:
            Tuple[bool, str, float]: (handoff_needed, target_agent, confidence)
        """
        # 1. Agent explicitly requests handoff in its response
        if response.get("suggested_next") and response["suggested_next"] != agent:
            target = response["suggested_next"].lower()
            if self.matrix.can_handoff(agent, target):
                return True, target, 0.9
                
        # 2. Low confidence in response
        confidence = response.get("confidence", 0.7)
        if confidence < 0.6:
            # Try to find a better agent
            classification = self.classify_fallback_agent(query, context, exclude=agent)
            if classification[0] != agent and self.matrix.can_handoff(agent, classification[0]):
                return True, classification[0], classification[1]
                
        # 3. User explicitly requests different help
        user_feedback = query.lower()
        transfer_phrases = [
            "talk to someone else",
            "different department",
            "transfer me",
            "speak with a different",
            "i need help with something else",
            "this isn't what i needed"
        ]
        
        if any(phrase in user_feedback for phrase in transfer_phrases):
            classification = self.classify_fallback_agent(query, context, exclude=agent)
            if classification[0] != agent and self.matrix.can_handoff(agent, classification[0]):
                return True, classification[0], 0.8
                
        return False, "", 0.0
        
    def execute_handoff(self, source_agent: str, target_agent: str, 
                       context: ConversationContext, query_data: Dict) -> Dict:
        """
        Perform the handoff from one agent to another
        
        Args:
            source_agent: Current agent
            target_agent: Agent to hand off to
            context: Conversation context
            query_data: Original query data
            
        Returns:
            Dict: Handoff result including transition message and status
        """
        # Validate the handoff first
        is_valid, reason = self.validator.validate_handoff(source_agent, target_agent, context)
        
        if not is_valid:
            logger.warning(f"Invalid handoff attempted: {source_agent} -> {target_agent}: {reason}")
            # If invalid, try another agent or stay with current
            alternative = self.find_alternative_target(source_agent, target_agent, context)
            if not alternative or alternative == source_agent:
                return {
                    "status": "no_handoff",
                    "message": "I'll continue assisting you with this.",
                    "agent": source_agent
                }
            target_agent = alternative
        
        # Get transition message
        transition_message = self.matrix.get_transition_message(source_agent, target_agent)
        
        # Record handoff in context
        context.record_handoff(source_agent, target_agent, "Agent handoff", 1.0)
        context.set_state(target_agent)
        
        # Prepare payload with updated context
        handoff_payload = {
            "text": query_data.get("text", ""),
            "context": context.serialize(),
            "history": context.get_last_n_exchanges(5)
        }
        
        return {
            "status": "handoff",
            "message": transition_message,
            "source": source_agent,
            "target": target_agent,
            "payload": handoff_payload
        }
    
    def classify_fallback_agent(self, query: str, context: ConversationContext, 
                              exclude: Optional[str] = None) -> Tuple[str, float]:
        """
        Classify which agent should handle a query when current agent can't
        
        Args:
            query: User query
            context: Conversation context
            exclude: Agent to exclude from consideration
            
        Returns:
            Tuple[str, float]: (agent_name, confidence)
        """
        query_lower = query.lower()
        
        # Simple rule-based classification - could be enhanced with ML
        
        # SQL Agent patterns (appointments, scheduling)
        sql_patterns = [
            r"\b(book|schedule|cancel|reschedule).*appointment\b",
            r"\b(register|sign up).*patient\b",
            r"\bdoctor\b.*\b(available|schedule|time|slot)\b",
            r"\b\d{1,2}:\d{2}\b",  # Match time format HH:MM
            r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
            r"\bappointment\b",
            r"\bschedule\b"
        ]
        
        # Medical/Graph patterns
        graph_patterns = [
            r"what should I do for.*",
            r"is.*serious",
            r"treatment for.*",
            r"my (child|son|daughter).*fever",
            r"symptoms? of.*",
            r"causes? of.*",
            r"prevention of.*",
            r"risks? of.*",
            r"complications? of.*",
            r"how to treat.*",
            r"how to prevent.*",
            r"what causes.*",
            r"what are the symptoms? of.*",
            r"how to manage.*",
            r"what is.*disease",
            r"what is.*condition",
            r"how to diagnose.*",
            r"what are the risk factors for.*"
        ]
        
        # Policy/RAG patterns
        rag_patterns = [
            r"policy (on|for|about)",
            r"hospital (policy|procedure)",
            r"visiting (hours|policy)",
            r"insurance",
            r"coverage",
            r"billing",
            r"payment",
            r"where (is|are) the",
            r"how do I find",
            r"directions to",
            r"parking"
        ]
        
        # Check patterns and keywords for each agent type
        sql_score = 0.0
        graph_score = 0.0
        rag_score = 0.0
        
        # Check SQL patterns
        for pattern in sql_patterns:
            if re.search(pattern, query_lower):
                sql_score += 0.3
                
        # Check GRAPH patterns
        for pattern in graph_patterns:
            if re.search(pattern, query_lower):
                graph_score += 0.3
                
        # Check RAG patterns
        for pattern in rag_patterns:
            if re.search(pattern, query_lower):
                rag_score += 0.3
                
        # SQL keywords
        sql_keywords = ["appointment", "schedule", "doctor", "booking", "slot", 
                      "time", "date", "register", "registration", "book", "cancel"]
        for keyword in sql_keywords:
            if keyword in query_lower:
                sql_score += 0.2
                
        # GRAPH keywords
        graph_keywords = ["symptom", "symptoms", "fever", "pain", "headache", "rash", 
                        "cough", "disease", "treatment", "genetic", "migraine", 
                        "diabetes", "hypertension", "asthma", "allergy", "sick", "ill"]
        for keyword in graph_keywords:
            if keyword in query_lower:
                graph_score += 0.2
                
        # RAG keywords
        rag_keywords = ["policy", "procedure", "visiting", "hours", "insurance", 
                      "billing", "payment", "directions", "parking", "location",
                      "cafeteria", "gift shop", "bathroom", "wifi"]
        for keyword in rag_keywords:
            if keyword in query_lower:
                rag_score += 0.2
                
        # Consider existing entities in conversation context
        if context.entities:
            if any(k in context.entities for k in ["date", "time", "doctor"]):
                sql_score += 0.3
                
            if any(k in context.entities for k in ["symptom", "disease", "condition"]):
                graph_score += 0.3
                
            if any(k in context.entities for k in ["policy", "location", "insurance"]):
                rag_score += 0.3
        
        # Normalize scores to max 1.0
        max_score = max(sql_score, graph_score, rag_score)
        if max_score > 1.0:
            sql_score = sql_score / max_score
            graph_score = graph_score / max_score
            rag_score = rag_score / max_score
            
        # Exclude specified agent
        if exclude == "sql":
            sql_score = 0
        elif exclude == "graph":
            graph_score = 0
        elif exclude == "rag":
            rag_score = 0
        
        # Get highest scoring agent
        scores = {
            "sql": sql_score,
            "graph": graph_score,
            "rag": rag_score
        }
        
        best_agent = max(scores, key=scores.get)
        return best_agent, scores[best_agent]
        
    def find_alternative_target(self, source_agent: str, invalid_target: str, 
                              context: ConversationContext) -> Optional[str]:
        """Find an alternative agent when the original target is invalid"""
        # Get valid targets for this source
        valid_targets = self.matrix.get_valid_targets(source_agent)
        
        # Remove the invalid target
        if invalid_target in valid_targets:
            valid_targets.remove(invalid_target)
            
        if not valid_targets:
            return None
            
        # Choose best alternative based on context
        scores = {}
        for target in valid_targets:
            # Check conversation entities for best match
            if target == "sql" and any(k in context.entities for k in ["date", "time", "doctor"]):
                scores[target] = 0.8
            elif target == "graph" and any(k in context.entities for k in ["symptom", "disease"]):
                scores[target] = 0.8
            elif target == "rag":
                scores[target] = 0.6  # Default fallback
            else:
                scores[target] = 0.5
                
        best_alternative = max(scores, key=scores.get)
        return best_alternative

class HandoffAnalytics:
    """Tracks handoff metrics and identifies improvement opportunities"""
    
    def __init__(self):
        self.handoffs = []
        
    def track_handoff(self, source: str, target: str, success_rate: float, resolution_time: float):
        """Log metrics for continuous improvement"""
        self.handoffs.append({
            "timestamp": None,  # Would use datetime.now() in real implementation
            "source_agent": source,
            "target_agent": target,
            "success_rate": success_rate,
            "resolution_time": resolution_time
        })
        
    def identify_bad_handoffs(self) -> List[Tuple[str, str]]:
        """Find handoff patterns that often fail"""
        bad_patterns = []
        
        # Group handoffs by source-target pair
        handoff_groups = {}
        for h in self.handoffs:
            key = (h["source_agent"], h["target_agent"])
            if key not in handoff_groups:
                handoff_groups[key] = []
            handoff_groups[key].append(h)
            
        # Identify patterns with low success rates
        for key, handoffs in handoff_groups.items():
            if len(handoffs) >= 5:  # Only consider patterns with sufficient data
                avg_success = sum(h["success_rate"] for h in handoffs) / len(handoffs)
                if avg_success < 0.5:
                    bad_patterns.append(key)
                    
        return bad_patterns
        
    def update_routing_rules(self, handoff_matrix: HandoffMatrix):
        """Adjust handoff matrix based on analytics"""
        bad_handoffs = self.identify_bad_handoffs()
        
        for source, target in bad_handoffs:
            if target in handoff_matrix.matrix.get(source, []):
                handoff_matrix.matrix[source].remove(target)
                logger.info(f"Removed bad handoff path: {source} -> {target} based on analytics")
