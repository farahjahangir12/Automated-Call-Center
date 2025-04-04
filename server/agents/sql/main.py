# Updated sql_agent.py with proper exports
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.memory import ConversationBufferMemory
from .prompt import agent_instructions
from .llm import llm
from .tools.doctors_details import doctor_info_tool
from .tools.cancel_appointment import cancel_appointment_tool
from .tools.book_appointment import book_appointment_tool
from .tools.register_patient import register_patient_tool
from .tools.appointmentSlots_info import appointment_slotsInfo_tool
from langchain_core.messages import SystemMessage
import asyncio

class SQLAgent:
    def __init__(self):
        # Initialize tools
        self.tools = self._initialize_tools()
        self.memory = self._initialize_memory()
        self.agent_executor = self._initialize_agent()

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
            if not hasattr(tool, '_run'):
                raise ValueError(f"Tool {tool.name} is missing required _run method")
        return tools

    def _initialize_memory(self):
        """Configure conversation memory"""
        return ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )

    def _initialize_agent(self):
        """Create and configure the agent executor"""
        # Ensure agent_instructions is in proper format
        system_content = agent_instructions.content if isinstance(agent_instructions, SystemMessage) else str(agent_instructions)
        
        prompt = ChatPromptTemplate.from_messages([
            {"role": "system", "content": system_content},  # API-compatible format
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        agent = create_openai_tools_agent(llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
            max_iterations=5  # Prevent infinite loops
        )

    async def handle_query(self, query: str) -> str:
        """Handle incoming queries with enhanced response parsing"""
        try:
            if query.lower() in ["bye", "exit", "goodbye"]:
                self.memory.clear()
                return "Goodbye! Have a nice day."
            
            memory_vars = self.memory.load_memory_variables({})
            if not isinstance(memory_vars.get("chat_history", []), list):
                self.memory.clear()
                
            response = await self.agent_executor.ainvoke({
                "input": query,
                "chat_history": memory_vars.get("chat_history", [])
            })
            
            # Enhanced response extraction
            if isinstance(response, dict):
                return response.get("output", response.get("result", "I didn't get a proper response."))
            return str(response)
            
        except Exception as e:
            self.memory.clear()
            error_msg = str(e)
            if "400" in error_msg or "message" in error_msg.lower():
                return "Sorry, I'm having trouble processing your request. Please try again."
            return f"System error: {error_msg}. Please try again."

# Router-compatible interface
async def handle_query(query: str) -> str:
    """
    Public interface for router compatibility
    Args:
        query (str): The user's query
    Returns:
        str: The agent's response
    """
    # Initialize agent if not already done
    if 'sql_agent_instance' not in globals():
        global sql_agent_instance
        sql_agent_instance = SQLAgent()
    
    try:
        response = await sql_agent_instance.handle_query(query)
        return response
    except Exception as e:
        return f"Appointment system error: {str(e)}. Please try again later."

def get_agent() -> SQLAgent:
    """Get the agent instance for routing system"""
    if 'sql_agent_instance' not in globals():
        global sql_agent_instance
        sql_agent_instance = SQLAgent()
    return sql_agent_instance

if __name__ == "__main__":
    # Test mode (unchanged)
    print("Appointment Management Agent - Test Mode")
    print("Type 'exit' to end the session\n")
    
    agent = SQLAgent()
    while True:
        try:
            user_input = input("Patient: ").strip()
            if not user_input:
                continue
                
            if user_input.lower() in ["exit", "bye"]:
                print("Agent: Goodbye!")
                break
                
            response = asyncio.run(agent.handle_query(user_input))
            print(f"Agent: {response}")
            
        except KeyboardInterrupt:
            print("\nSession ended by user")
            break
        except Exception as e:
            print(f"Critical error: {str(e)}")
            break