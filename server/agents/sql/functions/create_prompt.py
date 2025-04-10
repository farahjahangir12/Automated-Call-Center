from langchain.schema.runnable import RunnableSequence
from langchain.prompts import ChatPromptTemplate
from .llm import llm
from typing import Optional
import logging

logger = logging.getLogger(__name__)

async def create_prompt(system_message: str, user_input: str) -> str:
    """
    Creates a prompt template, invokes the LLM, and returns the response.
    Args:
        system_message: The system message to use in the prompt
        user_input: The user input to process
    Returns:
        str: The LLM's response
    """
    try:
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", "{input}")
        ])
        chain = RunnableSequence(prompt_template | llm)
        response = await chain.ainvoke({"input": user_input})
        return response.content.strip()
    except Exception as e:
        logger.error(f"Error in create_prompt: {e}")
        return ""

__all__ = ["create_prompt"]