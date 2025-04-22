import asyncio
import json
from main import MedicalGraphSystem

def print_banner():
    print("""
    ┌───────────────────────────────────────────────┐
    │         Graph Agent Standalone Tester         │
    └───────────────────────────────────────────────┘
    Type 'exit' to quit.
    """)

chat_history = []

async def main():
    agent = MedicalGraphSystem()
    print_banner()
    while True:
        user_input = input("\nYour Query: ").strip()
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("\nSession ended. Goodbye!")
            break
        if not user_input:
            print("Please enter a valid question.")
            continue
        response = await agent.handle_query({"text": user_input})
        print(f"\nAgent Response: {response['response']}")
        chat_history.append({
            "query": user_input,
            "response": response['response']
        })
    # Save chat history to file
    with open("graph_agent_chat_history.json", "w", encoding="utf-8") as f:
        json.dump(chat_history, f, ensure_ascii=False, indent=2)
    print("Chat history saved to graph_agent_chat_history.json")

if __name__ == "__main__":
    asyncio.run(main())
