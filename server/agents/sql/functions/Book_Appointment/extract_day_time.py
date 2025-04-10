from ...connection import supabase
from ...functions.create_prompt import create_prompt
import logging

logger = logging.getLogger(__name__)

# Function to extract the appointment day and time
async def extract_day_time(doctor_name: str, user_input: str) -> dict:
    """
    Extract and validate appointment day and time from user input.
    Args:
        doctor_name: Name of the doctor to check slots for
        user_input: String containing the potential appointment day and time
    Returns:
        dict: {
            'success': bool,
            'value': tuple or str,  # (doctor_id, day, time) if valid, error message if not
            'status': str,  # 'complete' or 'error'
            'available_slots': str  # formatted string of available slots
        }
    """
    try:
        # Step 1: Fetch doctor_id from the doctors table
        doctor_query = await supabase.table("doctors").select("doctor_id").eq("name", doctor_name).execute()

        if not doctor_query.data:
            return {
                'success': False,
                'value': f'No doctor found with name {doctor_name}',
                'status': 'error',
                'available_slots': ''
            }
        
        doctor_id = doctor_query.data[0]["doctor_id"]

        # Step 2: Fetch all available slots for the doctor
        slots_query = await supabase.table("doctors_slots").select("day, time").eq("doctor_id", doctor_id).execute()
        all_slots = {(slot["day"], slot["time"]) for slot in slots_query.data} if slots_query.data else set()

        # Step 3: Fetch booked slots from the appointments table
        booked_query = await supabase.table("appointments").select("appointment_day, appointment_time").eq("doctor_id", doctor_id).execute()
        booked_slots = {(slot["appointment_day"], slot["appointment_time"]) for slot in booked_query.data} if booked_query.data else set()

        # Step 4: Remove booked slots from available slots
        available_slots = all_slots - booked_slots

        # Step 5: Convert available slots to a formatted string
        if not available_slots:
            return {
                'success': False,
                'value': 'No available slots.',
                'status': 'error',
                'available_slots': ''
            }

        slots_str = ", ".join([f"{day} at {time[:-3]}" for day, time in sorted(available_slots)])  # Remove seconds from time

        if not user_input:
            return {
                'success': False,
                'value': 'Please provide the day and time for your appointment.',
                'status': 'error',
                'available_slots': slots_str
            }

        # Extract day and time using LLM
        day_time = await create_prompt(
            f"Extract only the day and time of the appointment from the following input."
            f"Available slots for the doctor are: {slots_str}. "
            f"Return the result in the format: 'Day at Time' only nothing else ."
            f"If the input does not match available slots, respond with: "
            f"'Sorry, this is not a valid date or time. Available slots are {slots_str}'.",
            user_input
        )
        day_time = day_time.strip()

        if day_time and "sorry" not in day_time.lower():
            parts = day_time.split(" at ")
            if len(parts) == 2:
                return {
                    'success': True,
                    'value': (doctor_id, parts[0], parts[1]),
                    'status': 'complete',
                    'available_slots': slots_str
                }

        return {
            'success': False,
            'value': f'Please select a valid time slot. Available slots are: {slots_str}',
            'status': 'error',
            'available_slots': slots_str
        }
    except Exception as e:
        logger.error(f"Error in extract_day_time: {e}")
        return {
            'success': False,
            'value': 'An error occurred while processing your request.',
            'status': 'error',
            'available_slots': ''
        }

__all__ = ["extract_day_time"]
