from ...connection import supabase

def delete_appointment(patient_id: str) -> bool:
    """
    Deletes the appointment associated with the given patient_id.
    """
    response = supabase.table("appointments").delete().eq("patient_id", patient_id).execute()

    return bool(response.data)

__all__ = ["delete_appointment"]