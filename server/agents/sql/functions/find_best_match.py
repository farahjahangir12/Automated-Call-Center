from connection import supabase
from rapidfuzz import process


def find_best_match(input_name: str) -> str:
    """
    Finds the most similar doctor name from the stored doctor list.

    :param input_name: The name to search for.
    :return: The best matching doctor name or an empty string if no match is found.
    """
    threshold = 70
    try:
        # Fetch all doctor names from Supabase
        response = supabase.table("doctors").select("name").execute()
        
        if not response.data:
            return ""  # Return an empty string if no data is found

        doctor_names = [doc["name"] for doc in response.data]

        best_match, score, _ = process.extractOne(input_name, doctor_names) if doctor_names else (None, 0, None)

        return best_match if score >= threshold else ""

    except Exception as e:
        print(f"Error: {e}")  # Log the error
        return ""  # Return an empty string in case of any exception

__all__ = ["find_best_match"]
