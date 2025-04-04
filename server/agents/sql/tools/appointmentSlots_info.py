from ..functions.Book_Appointment.extract_doctor_name import extract_doctor_name
from ..functions.AppointmentSlots_info.get_slots_info import get_slots_info
from langchain.tools import Tool


def get_appointment_slots(*args, **kwargs):
    """
    Extracts the doctor's name, fetches available slots, and returns them while ensuring booked slots are removed.
    """
    try:
        # Extract doctor name
        input =args[0] if args else ""

        doctor_name = extract_doctor_name(input)

        if not doctor_name:
            return {
                "observation": "Doctor name not found.",
                "action": "Error",
                "action_input": "Doctor name is missing or could not be extracted."
            }

        # Fetch available slots
        available_slots = get_slots_info(doctor_name)

        return {
            "observation": f"Available slots for Dr. {doctor_name} fetched successfully.",
            "action": "Final Answer",
            "action_input": available_slots
        }

    except Exception as e:
        return {
            "observation": f"An error occurred: {str(e)}",
            "action": "Error",
            "action_input": "There was an issue fetching appointment slots. Please try again."
        }

appointment_slotsInfo_tool = Tool(
    name="Appointment Slots  Detail",
    func=get_appointment_slots,
    description="Call this tool to cancel a patient's appointment by providing their patient ID."
)


__all__ = ["appointment_slotsInfo_tool"]
