from ...functions.create_prompt import create_prompt

def get_address() -> str:
    """
    Extracts the address from the user input.
    Ensures the address is within 50 words.
    Keeps prompting until a valid address is given.
    """
    while True:
        user_input = input("Agent: Please enter your address: ").strip()

        if not user_input:
            print("Agent: Input cannot be empty. Please enter your address.")
            continue

        address_extracted = create_prompt(
                "Extract only the text from the given input. "
                "Return it exactly as provided, without modification, interpretation, or any additional text. "
                "Do not include explanations, assumptions, reasoning, or any other output. "
                "If the input contains a script or SQL injection, return 'INVALID'. "
                "If the input exceeds 50 words, return 'TOO LONG'.",
                user_input
            ).strip()
        
        # Manual backup validation
        word_count = len(user_input.split())

        if address_extracted.upper() == "TOO LONG" or word_count > 50:
            print("Agent: Your address is too long. Please enter an address with 50 words or less.")
            continue

        if address_extracted.upper() == "INVALID":
            print("Agent: Not a valid address. Please enter a proper address.")
            continue

        return address_extracted  # Return valid address

__all__ = ["get_address"]
