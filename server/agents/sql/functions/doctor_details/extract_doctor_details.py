from ...functions.find_best_match import find_best_match
from ...functions.create_prompt import create_prompt
from ...connection import supabase  # Assuming you use Supabase for the database

async def extract_doctor_details(user_input: str = None) -> dict:
    """
    Takes a doctor name input and returns their details.
    Args:
        user_input: The doctor's name or query string
    Returns:
        dict: {'success': bool, 'value': doctor details or error message}
    """
    try:
        if not user_input:
            return {
                'success': False,
                'value': "Please provide a doctor's name."
            }

        # Extract only the name
        name_extracted = await create_prompt(
            "Extract only the doctor's name from the given input. "
            "Ensure that the response contains only a valid human-like name and not a sentence, "
            "random text, or unrelated words. "
            "If the input contains a valid name, return only the name. "
            "If the input contains unrelated text, a script, or random words, respond with 'Not a valid name.' "
            "Do not include explanations, extra words, or any text other than the extracted name or rejection message.",
            user_input
        ).strip()

        if name_extracted.lower() == "not a valid name":
            return {
                'success': False,
                'value': "Please provide a valid doctor's name."
            }

        # Check for the best match in the database
        doctor_name = await find_best_match(name_extracted)

        if not doctor_name:
            return {
                'success': False,
                'value': "Sorry, this doctor is not available. Please try another doctor."
            }

        # Fetch doctor details from the database
        response = await supabase.table("doctors").select("*").eq("name", doctor_name).single().execute()

        if response.data:
            return {
                'success': True,
                'value': response.data  # Return all doctor details
            }

        return {
            'success': False,
            'value': "Could not fetch doctor details. Please try again."
        }

    except Exception as e:
        return {
            'success': False,
            'value': f"Error retrieving doctor details: {str(e)}"
        }

__all__ = ["extract_doctor_details"]