from ..create_prompt import create_prompt
import re

def get_phoneNumber(user_input: str) -> dict:
    """
    Extract and validate a patient's phone number.
    Args:
        user_input: String containing the potential phone number
    Returns:
        dict: {
            'success': bool,
            'value': str,  # phone number if valid, error message if not
            'status': str  # 'complete' or 'error'
        }
    """
    if not user_input:
        return {
            'success': False,
            'value': 'Please provide your phone number.',
            'status': 'error'
        }
    
    # Clean and extract phone number using LLM
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
    
    # Validate the extracted number
    if phone_extracted == "Invalid" or not re.fullmatch(r"(\+92\d{10}|03\d{9})", phone_extracted):
        return {
            'success': False,
            'value': 'Please provide a valid Pakistani phone number (e.g., 03207673078 or +923207373878).',
            'status': 'error'
        }
    
    return {
        'success': True,
        'value': phone_extracted,
        'status': 'complete'
    }

__all__ = ["get_phoneNumber"]
