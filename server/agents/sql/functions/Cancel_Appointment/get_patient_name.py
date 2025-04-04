from ...connection import supabase

def get_patient_name(patient_id: str) -> str:
    """
    Retrieves the patient's name using their patient_id.
    """
    response = supabase.table("patients").select("name").eq("patient_id", patient_id).execute()

    if response.data:
        return response.data[0]["name"]
    return None

__all__ = ["get_patient_name"]