from ...functions.find_best_match import find_best_match
from ...functions.create_prompt import create_prompt
from ...connection import supabase  # Assuming you use Supabase for the database

def extract_doctor_details(user_input: str = None) -> dict:
    """
    Takes an optional doctor name input.
    If no input is given, prompts the user to enter the name.
    Extracts and validates the name, finds the best match, and retrieves doctor details.
    """
    while True:
        # If no input is given, prompt the user
        if not user_input:
            user_input = input("Agent: Please enter the name of the doctor: ").strip()

        # Validate input
        if not user_input:
            print("Agent: Input cannot be empty. Please enter a valid doctor's name.")
            user_input = None  # Reset input to prompt again
            continue

        # Extract only the name
        name_extracted = create_prompt(
            "Extract only the doctor's name from the given input. "
            "Ensure that the response contains only a valid human-like name and not a sentence, "
            "random text, or unrelated words. "
            "If the input contains a valid name, return only the name. "
            "If the input contains unrelated text, a script, or random words, respond with 'Not a valid name.' "
            "Do not include explanations, extra words, or any text other than the extracted name or rejection message.",
            user_input
        ).strip()

        if name_extracted.lower() == "not a valid name":
            print("Agent: Not a valid name. Please enter a valid doctor's name.")
            user_input = None  # Reset input to prompt again
            continue

        # Check for the best match in the database
        doctor_name = find_best_match(name_extracted)

        if not doctor_name:
            print("Agent: Sorry, this doctor is not available. Please enter a valid doctor's name.")
            user_input = None  # Reset input to prompt again
            continue

        # Fetch doctor details from the database
        response = supabase.table("doctors").select("*").eq("name", doctor_name).single().execute()

        if response.data:
            return response.data  # Return all doctor details as a dictionary

        print("Agent: Could not fetch doctor details. Please try again.")
        user_input = None  # Reset input to prompt again

__all__ = ["extract_doctor_details"]