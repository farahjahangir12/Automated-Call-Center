import asyncio
import importlib.util
import traceback
import sys
from pathlib import Path

# Add the FYP directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def debug_agent_loading(agent_name):
    print(f"\n=== Debugging {agent_name} agent loading ===\n")
    
    try:
        # Find the agent module
        agent_path = Path(__file__).parent / "agents" / agent_name / "main.py"
        print(f"Looking for agent module at {agent_path}")
        
        if not agent_path.exists():
            print(f"ERROR: Agent module not found at {agent_path}")
            return False
        print(f"Found agent module at {agent_path}")

        # Load the module using the correct package path
        print(f"Creating spec for {agent_name} agent")
        spec = importlib.util.spec_from_file_location(f"agents.{agent_name}.main", agent_path)
        if not spec or not spec.loader:
            print(f"ERROR: Failed to load spec for {agent_name} agent")
            return False
        print(f"Created spec for {agent_name} agent")

        print(f"Creating module from spec for {agent_name} agent")
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"agents.{agent_name}.main"] = module
        
        print(f"Executing module for {agent_name} agent")
        try:
            spec.loader.exec_module(module)
            print(f"Successfully executed module for {agent_name} agent")
        except Exception as module_error:
            print(f"ERROR: Error executing module for {agent_name} agent: {str(module_error)}")
            print(traceback.format_exc())
            return False

        # Check if get_agent function exists
        if not hasattr(module, 'get_agent'):
            print(f"ERROR: No get_agent function found in {agent_name} module")
            return False
        print(f"Found get_agent function in {agent_name} module")

        # Get agent instance using the factory method
        print(f"Getting agent instance for {agent_name} agent")
        try:
            agent = await module.get_agent()
            print(f"Got agent instance for {agent_name} agent")
        except Exception as agent_error:
            print(f"ERROR: Error getting agent instance for {agent_name} agent: {str(agent_error)}")
            print(traceback.format_exc())
            return False
        
        # Initialize the agent
        print(f"Initializing {agent_name} agent")
        try:
            await agent.initialize()
            print(f"Initialized {agent_name} agent")
        except Exception as init_error:
            print(f"ERROR: Error initializing {agent_name} agent: {str(init_error)}")
            print(traceback.format_exc())
            return False
        
        print(f"Successfully loaded {agent_name} agent")
        return True
    except Exception as e:
        print(f"ERROR: Failed to load {agent_name} agent: {str(e)}")
        print(f"Agent error traceback: {traceback.format_exc()}")
        return False

async def main():
    print("\n=== Agent Debugging Tool ===\n")
    
    # Debug only the SQL agent for now
    agent_name = "sql"
    success = await debug_agent_loading(agent_name)
    print(f"\nAgent {agent_name} loading result: {'SUCCESS' if success else 'FAILED'}\n")
    print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
