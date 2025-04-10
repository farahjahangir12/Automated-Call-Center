from ...functions.create_prompt import create_prompt

async def get_address(user_input: str) -> dict:
    """
    Extract and validate an address from the given input.
    Args:
        user_input: String containing the potential address
    Returns:
        dict: {
            'success': bool,
            'value': str,  # address if valid, error message if not
            'status': str  # 'complete' or 'error'
        }
    """
    if not user_input:
        return {
            'success': False,
            'value': 'Please provide your address.',
            'status': 'error'
        }
    
    # Extract and validate address using LLM
    address_extracted = await create_prompt(
        "Extract only the text from the given input. "
        "Return it exactly as provided, without modification, interpretation, or any additional text. "
        "Do not include explanations, assumptions, reasoning, or any other output. "
        "If the input contains a script or SQL injection, return 'INVALID'. "
        "If the input exceeds 50 words, return 'TOO LONG'.",
        user_input
    )
    address_extracted = address_extracted.strip()
    
    # Manual backup validation
    word_count = len(user_input.split())
    
    if address_extracted.upper() == "TOO LONG" or word_count > 50:
        return {
            'success': False,
            'value': 'Your address is too long. Please provide an address with 50 words or less.',
            'status': 'error'
        }
    
    if address_extracted.upper() == "INVALID":
        return {
            'success': False,
            'value': 'Not a valid address. Please provide a proper address.',
            'status': 'error'
        }
    
    return {
        'success': True,
        'value': address_extracted,
        'status': 'complete'
    }

__all__ = ["get_address"]
