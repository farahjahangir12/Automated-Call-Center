from ...connection import supabase


def get_appointment_details(patient_id: str):
    """
    Retrieves appointment details for the given patient_id.
    Extracts doctor name using doctor_id.
    """
    response = supabase.table("appointments").select("doctor_id", "appointment_day", "appointment_time").eq("patient_id", patient_id).execute()

    if not response.data:
        return None

    appointment = response.data[0]
    doctor_id = appointment["doctor_id"]

    # Fetch doctor's name
    doctor_response = supabase.table("doctors").select("name").eq("doctor_id", doctor_id).execute()

    if not doctor_response.data:
        return None

    doctor_name = doctor_response.data[0]["name"]
    return {
        "doctor_name": doctor_name,
        "day": appointment["appointment_day"],
        "time": appointment["appointment_time"]
    }
__all__ = ["get_appointment_details"]