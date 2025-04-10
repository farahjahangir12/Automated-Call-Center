from agents.sql.tools.functions.doctor_details.extract_doctor_details import extract_doctor_details
from langchain.tools import Tool
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

async def get_doctor_info(input_data: Dict) -> Dict:
    """
    Extract doctor information from input.
    Args:
        input_data: Dict containing query parameters
    Returns:
        Dict with doctor information or error message
    """
    try:
        # Extract doctor name
        input_str = input_data.get("input_str", "") if isinstance(input_data, dict) else str(input_data)
        result = await extract_doctor_details(input_str)

        if not result['success']:
            return {
                "output": result['value'],
                "current_step": "get_doctor",
                "collected_data": {},
                "status": "in_progress"
            }

        return {
            "output": f"Doctor information extracted successfully: {result['value']}",
            "current_step": "get_doctor",
            "collected_data": {"doctor": result['value']},
            "status": "in_progress"
        }
    except Exception as e:
        logger.error(f"Error in get_doctor_info: {str(e)}")
        return {
            "output": f"Error: {str(e)}",
            "current_step": "get_doctor",
            "collected_data": {},
            "status": "error"
        }

# Create tool instance
doctor_info_tool = Tool(
    name="Doctor Info",
    func=get_doctor_info,
    description="Use this tool to extract doctor information from user input.",
    output_key="output"
)

__all__ = ["doctor_info_tool"]
