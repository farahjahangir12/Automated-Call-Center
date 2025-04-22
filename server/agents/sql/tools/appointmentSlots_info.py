from agents.sql.tools.functions.book_appointment.extract_appointment_info import extract_appointment_info
from agents.sql.tools.functions.doctor_details.extract_doctor_details import extract_doctor_details
from agents.sql.tools.functions.appointmentSlots_info.get_available_slots import get_available_slots
from langchain.tools import Tool
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

async def get_appointment_slots(input_data: Dict) -> Dict:
    """
    Get available appointment slots for a doctor.
    Args:
        input_data: Dict containing query parameters
    Returns:
        Dict with available slots or error message
    """
    try:
        # Extract doctor name
        input_str = input_data.get("input_str", "") if isinstance(input_data, dict) else str(input_data)
        result = await extract_doctor_details(input_str)

        if not result['success']:
            return {
                "response": "Failed to extract doctor name.",
                "current_step": "get_doctor",
                "collected_data": {},
                "status": "error"
            }

        # Fetch available slots
        slots_result = await get_available_slots(result['value'])

        if not slots_result['success']:
            return {
                "response": "Failed to fetch appointment slots.",
                "current_step": "get_time",
                "collected_data": {},
                "status": "error"
            }

        return {
            "response": f"Available slots for Dr. {result['value']} fetched successfully: {slots_result['value']}",
            "current_step": "get_time",
            "collected_data": {"slots": slots_result['value']},
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error in get_appointment_slots: {str(e)}")
        return {
            "response": f"Error: {str(e)}",
            "current_step": "get_time",
            "collected_data": {},
            "status": "error"
        }

appointment_slotsInfo_tool = Tool(
    name="Appointment Slots Info",
    func=get_appointment_slots,
    description="Get available appointment slots for a specific doctor"
)

__all__ = ["appointment_slotsInfo_tool"]
