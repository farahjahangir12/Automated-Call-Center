from langchain.schema.runnable import RunnableSequence
from langchain.prompts import ChatPromptTemplate
from ..llm import llm  
# Define a function to create a prompt template
def create_prompt(system_message: str, user_input: str) -> str:
    """
    Creates a prompt template, invokes the LLM, and returns the response.
    """
    try:
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", "{input}")
        ])
        chain = RunnableSequence(prompt_template | llm)
        response = chain.invoke({"input": user_input})
        return response.content.strip()
    except Exception as e:
        print(f"Error in create_prompt: {e}")
        return ""

__all__ = ["create_prompt"]