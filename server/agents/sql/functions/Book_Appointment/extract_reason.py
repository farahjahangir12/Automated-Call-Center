from ...functions.create_prompt import create_prompt

# Function to extract the reason for the appointment
async def extract_reason(user_input: str) -> dict:
    """
    Extract and validate appointment reason from user input.
    Args:
        user_input: String containing the potential appointment reason
    Returns:
        dict: {
            'success': bool,
            'value': str,  # reason if valid, error message if not
            'status': str  # 'complete' or 'error'
        }
    """
    if not user_input:
        return {
            'success': False,
            'value': 'Please provide a reason for your appointment.',
            'status': 'error'
        }
    
    # Extract and validate reason using LLM
    reason = await create_prompt(
        "Extract and return only the main reason for the appointment exactly as provided by the user. "
        "Output only the extracted reason, without any additional text, descriptions, or explanations. "
        "Do NOT explain your thought process, do NOT clarify anything, and do NOT modify the user's wording. "
        "If the input is irrelevant or does not contain a valid reason, return: "
        "'Sorry, this is not a valid reason.'",
        user_input
    )
    
    if reason and "sorry" not in reason.lower():
        return {
            'success': True,
            'value': reason,
            'status': 'complete'
        }
    
    return {
        'success': False,
        'value': 'Please provide a valid reason for your appointment.',
        'status': 'error'
    }

__all__ = ["extract_reason"]