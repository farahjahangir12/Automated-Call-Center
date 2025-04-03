from functions.create_prompt import create_prompt
import re

def get_phoneNumber() -> str:
    """
    Extracts and validates a patient's phone number.
    Ensures the number follows the Pakistani standard:
    - 11 digits long, starting with '03' (e.g., 03207673078)
    - OR in international format, starting with '+92' followed by 10 digits (e.g., +923207373878).
    Keeps prompting until a valid phone number is given.
    """
    while True:
        user_input = input("Agent: Please tell your phone number: ").strip()

        if not user_input:
            print("Agent: Input cannot be empty. Please enter a valid phone number.")
            continue
        
        phone_extracted = create_prompt(
            "Extract only the phone number from the given input. "
            "Ensure the response contains only a valid Pakistani phone number. "
            "The number should be in one of the following formats:\n"
            "- Starts with '03' followed by exactly 9 digits \n"
            "- Starts with '+923' followed by exactly 9 digits \n"
            "If the input does not match these formats, return 'Invalid'. "
            "Return only the extracted phone number without any extra words, explanations, or modifications.",
            user_input
        ).strip()

       
        if phone_extracted == "Invalid" or not re.fullmatch(r"(\+92\d{10}|03\d{9})", phone_extracted):
            print("Agent: Not a valid phone number. Please enter a valid Pakistani number (e.g., 03207673078 or +923207373878).")
            continue

        return phone_extracted

__all__ = ["get_phoneNumber"]
