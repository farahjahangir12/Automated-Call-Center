from functions.create_prompt import create_prompt

def get_gender() -> str:
    """
    Extracts the gender (Male, Female, or Prefer not to say).
    Returns 'M' for Male, 'F' for Female, 'N' for Prefer not to say.
    Keeps prompting until a valid input is given.
    """
    while True:
        user_input = input("Agent: Please tell your gender: ").strip().lower()

        if not user_input:
            print("Agent: Input cannot be empty. Please enter your gender.")
            continue

        # Use AI to extract gender
        gender_extracted = create_prompt(
            "Extract the gender from the given input. "
            "User can say 'Male', 'Female', or 'Prefer not to say'. "
            "Return exactly 'M' for Male, 'F' for Female, or 'N' for Prefer not to say. "
            "If the input does not match these categories, return 'Invalid'. "
            "Do not return any other words or explanations.",
            user_input
        ).strip().upper()

       
        if gender_extracted == "INVALID":
            if user_input in {"male", "m"}:
                return "M"
            elif user_input in {"female", "f"}:
                return "F"
            elif user_input in {"prefer not to say", "prefer not"}:
                return "N"

            print("Agent: Not a valid gender. Please say 'Male', 'Female', or 'Prefer not to say'.")
            continue
        
        return gender_extracted  

__all__ = ["get_gender"]
