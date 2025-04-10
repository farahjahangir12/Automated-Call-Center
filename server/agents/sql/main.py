import traceback
import sys
import os
from pathlib import Path

# Add the FYP directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.memory import ConversationBufferMemory
from langchain.tools import StructuredTool
from agents.sql.prompt import agent_instructions
from agents.sql.llm import llm
from agents.sql.tools.doctors_details import doctor_info_tool
from agents.sql.tools.cancel_appointment import cancel_appointment_tool
from agents.sql.tools.book_appointment import AppointmentBookingTool, AppointmentBookingInput
from agents.sql.tools.register_patient import register_patient_tool
from agents.sql.tools.appointmentSlots_info import appointment_slotsInfo_tool
from agents.sql.connection import supabase
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import asyncio
import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime
import json

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create handlers for both file and console output
file_handler = logging.FileHandler('sql_agent_debug.log')
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

class SQLAgent:
    def __init__(self, session_context: Optional[Dict] = None):
        """Initialize with optional session context"""
        logger.info("Creating SQL Agent instance")
        self.session_context = session_context or {}
        logger.debug(f"Initial session context: {self.session_context}")
        self._initialized = False
        self.tools = None
        self.memory = None
        self.agent_executor = None
    
    @classmethod
    async def create(cls, session_context: Optional[Dict] = None) -> 'SQLAgent':
        """Factory method to create and initialize a SQLAgent instance"""
        try:
            logger.info("Creating SQL Agent instance")
            self = cls(session_context)
            await self.initialize()
            return self
        except Exception as e:
            logger.error(f"Error creating SQL Agent: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def initialize(self) -> None:
        """Asynchronously initialize the agent"""
        if self._initialized:
            return

        try:
            # Initialize Supabase connection
            logger.info("Initializing Supabase connection")
            await supabase.initialize()

            # Initialize tools
            logger.info("Initializing tools")
            booking_tool = AppointmentBookingTool(
                doctor_info_tool=doctor_info_tool,
                appointmentSlots_info_tool=appointment_slotsInfo_tool
            )
            
            self.tools = [
                doctor_info_tool,
                cancel_appointment_tool,
                StructuredTool.from_function(
                    booking_tool.invoke,
                    name="book_appointment_tool",
                    description="Handle appointment booking requests. This tool manages the entire booking process interactively, guiding the user through selecting a doctor, checking availability, and confirming the appointment.",
                    args_schema=AppointmentBookingInput
                ),
                register_patient_tool,
                appointment_slotsInfo_tool
            ]
            logger.debug(f"Tools initialized: {len(self.tools)}")

            # Initialize memory with session context
            logger.info("Initializing memory")
            self.memory = self._initialize_memory()
            logger.debug("Memory initialized")

            # Create prompt template
            logger.info("Creating prompt template")
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=agent_instructions),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad")
            ])

            # Create agent with proper tool input handling
            logger.info("Creating agent")
            agent = create_openai_tools_agent(
                llm=llm,
                tools=self.tools,
                prompt=prompt
            )

            # Create agent executor
            logger.info("Creating agent executor")
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                memory=self.memory,
                verbose=True,
                handle_parsing_errors=True,
                return_intermediate_steps=True,
                max_iterations=5,
                max_execution_time=30.0
            )

            # Mark as initialized
            self._initialized = True
            logger.info("SQL Agent initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing SQL Agent: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def verify(self) -> bool:
        """Verify agent is properly initialized"""
        if not self._initialized:
            return False
        
        checks = [
            self.tools is not None,
            self.memory is not None,
            self.agent_executor is not None
        ]
        
        if not all(checks):
            logger.error("SQL Agent verification failed: Missing required components")
            return False
            
        return True

    def _initialize_tools(self):
        """Initialize and validate all tools"""
        tools = [
            doctor_info_tool,
            appointment_slotsInfo_tool,
            book_appointment_tool,  
            register_patient_tool,
            cancel_appointment_tool
        ]

        for tool in tools:
            if not hasattr(tool, 'name'):
                raise ValueError(f"Tool {tool} is not properly initialized")
            if not hasattr(tool, 'coroutine') and not hasattr(tool, '_run'):
                raise ValueError(f"Tool {tool.name} is missing required coroutine/run method")
        return tools

    def _initialize_memory(self):
        """Configure conversation memory with session context"""
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )
        
        # Load previous conversation if exists in session
        if "chat_history" in self.session_context:
            for exchange in self.session_context["chat_history"]:
                if "query" in exchange and "response" in exchange:
                    memory.chat_memory.add_message(HumanMessage(content=exchange["query"]))
                    memory.chat_memory.add_message(AIMessage(content=exchange["response"]))
        
        return memory

    async def handle_query(self, query_data: Dict) -> Dict:
        """
        Handle incoming queries with session support
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
        logger.info("SQL Agent: Received query")
        logger.debug(f"Query data: {query_data}")
        
        try:
            # Update session context if provided
            if "context" in query_data:
                self.session_context.update(query_data["context"])
                logger.debug(f"Updated session context: {self.session_context}")
            
            # Add the current query to memory
            if query_data.get("text"):
                self.memory.chat_memory.add_message(HumanMessage(content=query_data["text"]))
            
            # Get the current chat history as a list of messages
            chat_history = self.memory.chat_memory.messages
            
            # Prepare input for agent executor with proper tool input format
            agent_input = {
                "input": query_data["text"],
                "chat_history": chat_history,
                "context": self.session_context
            }
            
            # Invoke the agent with proper input format
            response = await self.agent_executor.ainvoke({"input": query_data["text"]})
            
            # Extract response text
            response_text = response["output"]
            
            # Extract context updates from response
            context_updates = self._extract_context_updates(response_text)
            
            # Add AI response to memory
            if response_text:
                self.memory.chat_memory.add_message(AIMessage(content=response_text))
            
            return {
                "response": response_text,
                "context_updates": context_updates,
                "suggested_next": None
            }
        except Exception as e:
            logger.error(f"Error in SQL Agent handle_query: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "response": f"Appointment system error: {str(e)}. Please try again later.",
                "context_updates": {},
                "suggested_next": "HUMAN"
            }

    def _extract_context_updates(self, response_text: str) -> Dict:
        """Extract potential context updates from agent response"""
        updates = {}
        
        # Detect patient registration
        if "successfully registered" in response_text.lower():
            updates["status"] = "registered"
            # Extract patient ID if possible
            id_match = re.search(r"ID:? (\d+)", response_text)
            if id_match:
                updates["patient_id"] = id_match.group(1)
        
        # Detect appointment booking
        elif "appointment booked" in response_text.lower() or "appointment confirmed" in response_text.lower():
            updates["last_action"] = "appointment_booking"
            # Extract appointment details if possible
            date_match = re.search(r"on (\d{4}-\d{2}-\d{2})", response_text)
            if date_match:
                updates["last_appointment"] = date_match.group(1)
        
        return updates

# Router-compatible interface
# Configure logging
logger = logging.getLogger(__name__)

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
    logger.info("SQL Agent: Received query")
    logger.debug(f"Query data: {query_data}")
    
    try:
        # Get or create agent instance
        agent = await get_agent()
        
        # Ensure agent is initialized
        if not agent._initialized:
            logger.info("Initializing SQL Agent")
            await agent.initialize()
        
        # Update context if provided
        if "context" in query_data:
            agent.session_context.update(query_data["context"])
            logger.debug(f"Updated session context: {agent.session_context}")
        
        logger.info("Forwarding query to SQL Agent instance")
        response = await agent.handle_query(query_data)
        logger.info("Received response from SQL Agent instance")
        logger.debug(f"Agent response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error in SQL Agent handle_query: {str(e)}")
        return {
            "response": f"Appointment system error: {str(e)}. Please try again later.",
            "context_updates": {},
            "suggested_next": "HUMAN"
        }

async def get_agent() -> SQLAgent:
    """Get the agent instance for routing system"""
    if 'sql_agent_instance' not in globals():
        global sql_agent_instance
        sql_agent_instance = await SQLAgent.create()
    return sql_agent_instance

if __name__ == "__main__":
    # Test mode with basic session simulation
    print("Appointment Management Agent - Test Mode")
    print("Type 'exit' to end the session\n")
    
    async def async_main():
        agent = SQLAgent()
        while True:
            try:
                user_input = input("Patient: ").strip()
                if not user_input:
                    continue
                    
                if user_input.lower() in ["exit", "bye"]:
                    print("Agent: Goodbye!")
                    break
                    
                response = await agent.handle_query({"text": user_input})
                print(f"Agent: {response['response']}")
                
            except KeyboardInterrupt:
                print("\nSession ended by user")
                break
            except Exception as e:
                print(f"Critical error: {str(e)}")
                break

    asyncio.run(async_main())