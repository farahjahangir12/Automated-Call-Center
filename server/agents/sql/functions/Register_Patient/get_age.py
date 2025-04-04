import re
from ...functions.create_prompt import create_prompt

def get_age() -> int:
    """
    Extracts the age from the user input, ensuring it is a valid number between 1 and 100.
    """
    while True:
        user_input = input("Agent: Please enter your age: ").strip()

  
        if not any(char.isdigit() for char in user_input):
            print("Agent: Please enter a valid number for age.")
            continue

       
        age_extracted = create_prompt(
            "Extract the numeric age from the input. "
            "Return only the number without any explanations, context, or additional text. "
            "Do NOT include any reasoning, interpretations, or words—ONLY the number.",
            user_input
        ).strip()

       
        extracted_numbers = re.findall(r"\d+", age_extracted)
        if extracted_numbers:
            age = int(extracted_numbers[0]) 

            if 1 <= age <= 100:
                return age
            else:
                print("Agent: Age must be between 1 and 100. Please enter a valid age.")
        else:
            print("Agent: Please enter a valid age.")

__all__ = ["get_age"]
