from functions.create_prompt import create_prompt

def get_name() -> str:
    """
    Extract the name from the user input
    """
    while True:
        user_input = input("Agent: Please tell your name: ").strip()
        
        if not user_input:
            print("Agent: Input cannot be empty. Please enter a valid doctor's name.")
            continue
        
        # # Extract only the name
        name_extracted = create_prompt(
        "Extract only the name from the given input. "
        "Ensure that the response contains only a valid human-like name and not a sentence, "
        "random text, or unrelated words. "
        "If the input contains a valid name, return only the name. "
        "If the input contains unrelated text, a script, or random words, respond with 'Not a valid name.' "
        "Do not include explanations, extra words, or any text other than the extracted name or rejection message.",
        user_input
        ).strip()


        # if "Not" in name_extracted.lower():
        #     print("Agent: Not a valid name. Please say a valid  name.")
        #     continue
        # else:

        return name_extracted


__all__ = ["get_name"]