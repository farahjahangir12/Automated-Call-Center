from ...functions.create_prompt import create_prompt

def get_name(user_input: str) -> dict:
    """
    Extract and validate a name from the given input.
    Args:
        user_input: String containing the potential name
    Returns:
        dict: {
            'success': bool,
            'value': str,  # extracted name if valid, error message if not
            'status': str  # 'complete' or 'error'
        }
    """
    if not user_input:
        return {
            'success': False,
            'value': 'Please provide your name.',
            'status': 'error'
        }
    
    # Extract only the name
    name_extracted = create_prompt(
        "Extract only the name from the given input. "
        "Ensure that the response contains only a valid human-like name and not a sentence, "
        "random text, or unrelated words. "
        "If the input contains a valid name, return only the name. "
        "If the input contains unrelated text, a script, or random words, respond with 'Not a valid name.' "
        "Do not include explanations, extra words, or any text other than the extracted name or rejection message.",
        user_input
    ).strip()

    if 'Not' in name_extracted:
        return {
            'success': False,
            'value': 'Please provide a valid name.',
            'status': 'error'
        }
    
    return {
        'success': True,
        'value': name_extracted,
        'status': 'complete'
    }


__all__ = ["get_name"]