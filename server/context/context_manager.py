from typing import Dict, Any, Optional
from datetime import datetime
import json
from pathlib import Path

class ContextManager:
    def __init__(self):
        self._context = {}
        self._agent_states = {
            "rag": {},
            "sql": {},
            "graph": {}
        }
        
    def update_context(self, agent_id: str, updates: Dict[str, Any]) -> None:
        """Update context for a specific agent and merge shared context"""
        # Update agent-specific state
        self._agent_states[agent_id].update(updates)
        
        # Extract and merge shared context
        shared_context = self._extract_shared_context(updates)
        if shared_context:
            self._context.update(shared_context)
            
    def get_context(self, agent_id: str) -> Dict[str, Any]:
        """Get combined context for an agent (shared + agent-specific)"""
        return {
            **self._context,  # Shared context
            **self._agent_states[agent_id]  # Agent-specific context
        }
    
    def _extract_shared_context(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Extract context that should be shared across agents"""
        shared_context = {}
        
        # Patient information should be shared
        if "patient_id" in updates:
            shared_context["patient_id"] = updates["patient_id"]
        if "patient_name" in updates:
            shared_context["patient_name"] = updates["patient_name"]
            
        # Medical context should be shared
        if "symptoms" in updates:
            shared_context["reported_symptoms"] = updates["symptoms"]
        if "diagnosis" in updates:
            shared_context["current_diagnosis"] = updates["diagnosis"]
            
        # Appointment context should be shared
        if "last_appointment" in updates:
            shared_context["last_appointment"] = updates["last_appointment"]
        if "next_appointment" in updates:
            shared_context["next_appointment"] = updates["next_appointment"]
            
        # Department context should be shared
        if "department" in updates:
            shared_context["current_department"] = updates["department"]
            
        return shared_context
    
    def clear_context(self, agent_id: Optional[str] = None) -> None:
        """Clear context for a specific agent or all context if agent_id is None"""
        if agent_id:
            self._agent_states[agent_id].clear()
        else:
            self._context.clear()
            for state in self._agent_states.values():
                state.clear()
                
    def save_state(self, file_path: str) -> None:
        """Save the current context state to a file"""
        state = {
            "shared_context": self._context,
            "agent_states": self._agent_states,
            "timestamp": datetime.now().isoformat()
        }
        Path(file_path).write_text(json.dumps(state, indent=2))
        
    def load_state(self, file_path: str) -> None:
        """Load context state from a file"""
        if Path(file_path).exists():
            state = json.loads(Path(file_path).read_text())
            self._context = state.get("shared_context", {})
            self._agent_states = state.get("agent_states", {
                "rag": {},
                "sql": {},
                "graph": {}
            })
