"""
Context Management System for Hospital Router

This module maintains conversation context across sessions and provides
storage and retrieval mechanisms for context objects.
"""

import logging
import uuid
from typing import Dict, Optional, Any
from conversation_context import ConversationContext

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class ContextManager:
    """Manages conversation contexts for the hospital router system"""
    
    def __init__(self):
        """Initialize the context manager"""
        self.contexts = {}  # In-memory storage of context objects
        logger.info("ContextManager initialized")
        
    def get_context(self, context_id: str) -> Optional[ConversationContext]:
        """
        Retrieve a context by ID
        
        Args:
            context_id: Unique identifier for the context
            
        Returns:
            ConversationContext if found, None otherwise
        """
        if context_id in self.contexts:
            logger.debug(f"Retrieved context {context_id}")
            return self.contexts[context_id]
        logger.warning(f"Context {context_id} not found")
        return None
        
    def save_context(self, context: ConversationContext) -> str:
        """
        Save a context object
        
        Args:
            context: ConversationContext object to save
            
        Returns:
            String ID of the saved context
        """
        if not hasattr(context, '_context_id'):
            # Assign a new ID if not present
            context._context_id = str(uuid.uuid4())
            
        context_id = context._context_id
        self.contexts[context_id] = context
        logger.debug(f"Saved context {context_id}")
        return context_id
        
    def delete_context(self, context_id: str) -> bool:
        """
        Delete a context by ID
        
        Args:
            context_id: ID of context to delete
            
        Returns:
            True if deleted, False if not found
        """
        if context_id in self.contexts:
            del self.contexts[context_id]
            logger.debug(f"Deleted context {context_id}")
            return True
        logger.warning(f"Context {context_id} not found for deletion")
        return False
        
    def clear_context(self) -> None:
        """Clear all contexts from memory"""
        self.contexts = {}
        logger.debug("Cleared all contexts")
        
    def create_new_context(self) -> ConversationContext:
        """
        Create a new empty context
        
        Returns:
            New ConversationContext instance with ID assigned
        """
        context = ConversationContext()
        self.save_context(context)
        logger.debug(f"Created new context {context._context_id}")
        return context
