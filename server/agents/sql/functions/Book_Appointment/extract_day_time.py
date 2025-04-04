from ...connection import supabase
from ...functions.create_prompt import create_prompt

# Function to extract the appointment day and time
def extract_day_time(doctor_name: str) -> tuple:
    """
    Prompts the user to enter the day and time of the appointment and validates the input.
    """

    # Step 1: Fetch doctor_id from the doctors table
    doctor_query = supabase.table("doctors").select("doctor_id").eq("name", doctor_name).execute()

    if not doctor_query.data:
        return f"No doctor found with name {doctor_name}", None
    
    doctor_id = doctor_query.data[0]["doctor_id"]

    # Step 2: Fetch all available slots for the doctor
    slots_query = supabase.table("doctors_slots").select("day, time").eq("doctor_id", doctor_id).execute()
    all_slots = {(slot["day"], slot["time"]) for slot in slots_query.data} if slots_query.data else set()

    # Step 3: Fetch booked slots from the appointments table
    booked_query = supabase.table("appointments").select("appointment_day, appointment_time").eq("doctor_id", doctor_id).execute()
    booked_slots = {(slot["appointment_day"], slot["appointment_time"]) for slot in booked_query.data} if booked_query.data else set()

    # Step 4: Remove booked slots from available slots
    available_slots = all_slots - booked_slots

    # Step 5: Convert available slots to a formatted string
    if available_slots:
        slots_str = ", ".join([f"{day} at {time[:-3]}" for day, time in sorted(available_slots)])  # Remove seconds from time
    else:
        return "No available slots.", None

    # Step 6: Prompt user for day and time
    while True:
        user_input = input("Agent: Please provide the day and time of your appointment: ").strip()

        if not user_input:
            print("Agent: Input cannot be empty. Please enter a valid date and time.")
            continue

        # Step 7: Pass the formatted slots data into the system prompt
        day_time = create_prompt(
            f"Extract only the day and time of the appointment from the following input."
            f"Available slots for the doctor are: {slots_str}. "
            f"Return the result in the format: 'Day at Time' only nothing else ."
            f"If the input does not match available slots, respond with: "
            f"'Sorry, this is not a valid date or time. Available slots are {slots_str}'.",
            user_input
        ).strip()

        if day_time and "sorry" not in day_time.lower():
            parts = day_time.split(" at ")  
            if len(parts) == 2:
                return doctor_id,parts[0], parts[1]  # Return as (day, time)

        else:
            print(f"Agent: {day_time}")  # Print the error message and ask again

__all__ = ["extract_day_time"]
