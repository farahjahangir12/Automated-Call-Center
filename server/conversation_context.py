"""
Conversation Context Manager for Agent Handoffs

This module implements a robust conversation context preservation system
that maintains history, extracted entities, and state across agent handoffs.
"""

class ConversationContext:
    def __init__(self):
        self.history = []  # Full conversation history
        self.entities = {}  # Extracted entities (dates, symptoms, etc.)
        self.current_state = None  # Current dialog state
        self.previous_agents = []  # Which agents handled this conversation
        self.confidence_scores = {}  # Confidence scores for each agent
        self.handoff_count = 0  # Number of handoffs in this conversation
        self.last_handoff_reason = None  # Why the last handoff occurred
        self.user_preferences = {}  # User preferences identified during conversation
        
    def add_history_item(self, role, content):
        """Add an item to the conversation history"""
        self.history.append({"role": role, "content": content})
        return self
        
    def add_entity(self, entity_type, entity_value, confidence=1.0):
        """Add an extracted entity with confidence score"""
        if entity_type not in self.entities:
            self.entities[entity_type] = []
            
        # Check if entity already exists to avoid duplicates
        for existing in self.entities[entity_type]:
            if existing["value"] == entity_value:
                # Update confidence if new one is higher
                if confidence > existing["confidence"]:
                    existing["confidence"] = confidence
                return self
                
        # Add new entity
        self.entities[entity_type].append({
            "value": entity_value, 
            "confidence": confidence,
            "source_agent": self.current_state
        })
        return self
        
    def set_state(self, state):
        """Update the current state and track agent history"""
        if self.current_state and self.current_state != state:
            if self.current_state not in self.previous_agents:
                self.previous_agents.append(self.current_state)
            self.handoff_count += 1
            
        self.current_state = state
        return self
        
    def record_handoff(self, from_agent, to_agent, reason, success_score=1.0):
        """Record a handoff event with reason and success score"""
        self.last_handoff_reason = reason
        self.history.append({
            "role": "system",
            "content": f"HANDOFF: {from_agent} → {to_agent}",
            "metadata": {
                "handoff_reason": reason,
                "success_score": success_score,
                "handoff_number": self.handoff_count
            }
        })
        return self
        
    def update_confidence(self, agent, score):
        """Update confidence score for an agent"""
        self.confidence_scores[agent] = score
        return self
        
    def is_first_interaction(self):
        """Check if this is the first interaction with the system"""
        return len(self.history) == 0
        
    def get_summary(self):
        """Get a summary of the conversation context for handoffs"""
        return {
            "history_length": len(self.history),
            "current_state": self.current_state,
            "previous_agents": self.previous_agents,
            "entities": self.entities,
            "handoff_count": self.handoff_count,
            "last_handoff_reason": self.last_handoff_reason,
            "confidence_scores": self.confidence_scores
        }
        
    def get_last_n_exchanges(self, n=3):
        """Get the last N conversation exchanges for context"""
        return self.history[-n:] if len(self.history) >= n else self.history
        
    def serialize(self):
        """Serialize context for storage"""
        return {
            "history": self.history,
            "entities": self.entities,
            "current_state": self.current_state,
            "previous_agents": self.previous_agents,
            "handoff_count": self.handoff_count,
            "confidence_scores": self.confidence_scores,
            "user_preferences": self.user_preferences
        }
        
    @classmethod
    def deserialize(cls, data):
        """Create context from serialized data"""
        context = cls()
        context.history = data.get("history", [])
        context.entities = data.get("entities", {})
        context.current_state = data.get("current_state")
        context.previous_agents = data.get("previous_agents", [])
        context.handoff_count = data.get("handoff_count", 0)
        context.confidence_scores = data.get("confidence_scores", {})
        context.user_preferences = data.get("user_preferences", {})
        return context
