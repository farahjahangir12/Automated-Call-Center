from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentType, initialize_agent
from langchain.memory import ConversationBufferMemory
from prompt import agent_instructions
from llm import llm
from tools.doctors_details import doctor_info_tool
from tools.cancel_appointment import cancel_appointment_tool
from tools.book_appointment import book_appointment_tool
from tools.register_patient import register_patient_tool
from tools.appointmentSlots_info import appointment_slotsInfo_tool





# Define Memory for Conversation History
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

prompt = ChatPromptTemplate.from_messages(
    [    agent_instructions,
        MessagesPlaceholder("chat_history", optional=True),  
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),  
    ]
)

agent = initialize_agent(
    tools=[doctor_info_tool,appointment_slotsInfo_tool,book_appointment_tool,register_patient_tool,cancel_appointment_tool],
    llm=llm,
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=True,
    prompt=prompt,
     handle_parsing_errors=True  # Automatically retries if parsing fails

)


# Continuous Interaction Loop
while True:
    # print(memory)
    user_input = input("You: ")  
    if user_input.lower() == "bye":
        print("Agent: Goodbye!")
        break 
    response = agent.invoke({"input": user_input, "chat_history": memory.load_memory_variables({})})

    print(f"Agent: {response['output']}")  

    