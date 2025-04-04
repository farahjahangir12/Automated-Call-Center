from ...functions.find_best_match import find_best_match
from ...functions.create_prompt import create_prompt

def extract_doctor_name(user_input: str = None) -> str:
    """
    Prompts the user to enter the doctor's name, validates the input, 
    and checks for the best match in the database.
    """
    while True:
        if not user_input:
            user_input = input("Agent: Please enter the name of the doctor: ").strip()

        # Validate input
        if not user_input:
            print("Agent: Input cannot be empty. Please enter a valid doctor's name.")
            user_input = None  # Reset input to prompt again
            continue
        
        # # Extract only the name
        name_extracted = create_prompt(
        "Extract only the doctor's name from the given input. "
        "Ensure that the response contains only a valid human-like name and not a sentence, "
        "random text, or unrelated words. "
        "If the input contains a valid name, return only the name. "
        "If the input contains unrelated text, a script, or random words, respond with 'Not a valid name.' "
        "Do not include explanations, extra words, or any text other than the extracted name or rejection message.",
        user_input
        ).strip()


        # if "sorry" in name_extracted.lower():
        #     print("Agent: Not a valid name. Please enter a valid doctor's name.")
        #     continue

  

        # Check for best match in database
        doctor_name = find_best_match(name_extracted)

        if doctor_name:
            return doctor_name

        user_input=None
        print("Agent: Sorry, this doctor is not available. Please enter a valid doctor's name.")

__all__ = ["extract_doctor_name"]