from functions.create_prompt import create_prompt



# Function to extract the reason for the appointment
def extract_reason() -> str:
    """
    Prompts the user to enter the reason for the appointment and validates the input.
    """
    while True:
        user_input = input("Agent: What is the reason for your appointment? ").strip()
        if not user_input:
            print("Agent: Input cannot be empty. Please enter a valid reason.")
            continue
        reason = create_prompt(
        f"Extract and return only the main reason for the appointment exactly as provided by the user. "
        f"Output only the extracted reason, without any additional text, descriptions, or explanations. "
        f"Do NOT explain your thought process, do NOT clarify anything, and do NOT modify the user’s wording. "
        f"If the input is irrelevant or does not contain a valid reason, return: "
        f"'Sorry, this is not a valid reason.'",
        user_input
    )

        
        if reason and "sorry" not in reason.lower():
            return reason
        print("Agent: Sorry, this is not a valid reason. Please enter a proper reason for your appointment.")

__all__ = ["extract_reason"]