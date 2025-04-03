from connection import supabase

def get_slots_info(doctor_name: str):
    """
    Fetches available appointment slots for a given doctor (searched by name), excluding booked slots.
    """
    try:
        # Fetch doctor_id using doctor_name
        doctor_response = (
            supabase
            .from_("doctors")
            .select("doctor_id")
            .eq("name", doctor_name)
            .single()
            .execute()
        )

        if not doctor_response.data:
            return f"Doctor '{doctor_name}' not found."

        doctor_id = doctor_response.data["doctor_id"]

        # Fetch all available slots
        slots_query = (
            supabase
            .from_("doctors_slots")
            .select("day, time")
            .eq("doctor_id", doctor_id)
            .execute()
        )
        all_slots = {(slot["day"], slot["time"]) for slot in slots_query.data} if slots_query.data else set()

        # Fetch booked slots
        booked_query = (
            supabase
            .from_("appointments")
            .select("appointment_day, appointment_time")
            .eq("doctor_id", doctor_id)
            .execute()
        )
        booked_slots = {(slot["appointment_day"], slot["appointment_time"]) for slot in booked_query.data} if booked_query.data else set()

        # Calculate available slots
        available_slots = all_slots - booked_slots

        return list(sorted(available_slots)) if available_slots else f"No available slots for Dr. {doctor_name}."

    except Exception as e:
        return f"Error fetching slots: {str(e)}"

__all__ = ["get_slots_info"]
