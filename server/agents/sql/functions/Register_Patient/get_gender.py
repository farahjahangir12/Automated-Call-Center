from ...functions.create_prompt import create_prompt

async def get_gender(user_input: str) -> dict:
    """
    Extract and validate gender from the given input.
    Args:
        user_input: String containing the potential gender
    Returns:
        dict: {
            'success': bool,
            'value': str,  # 'M', 'F', or 'N' if valid, error message if not
            'status': str  # 'complete' or 'error'
        }
    """
    if not user_input:
        return {
            'success': False,
            'value': 'Please provide your gender (Male, Female, or Prefer not to say).',
            'status': 'error'
        }
    
    user_input = user_input.lower().strip()
    
    # First try direct matching
    if user_input in {"male", "m"}:
        return {'success': True, 'value': 'M', 'status': 'complete'}
    elif user_input in {"female", "f"}:
        return {'success': True, 'value': 'F', 'status': 'complete'}
    elif user_input in {"prefer not to say", "prefer not", "n"}:
        return {'success': True, 'value': 'N', 'status': 'complete'}
    
    # Use AI to extract gender for more complex inputs
    gender_extracted = await create_prompt(
        "Extract the gender from the given input. "
        "User can say 'Male', 'Female', or 'Prefer not to say'. "
        "Return exactly 'M' for Male, 'F' for Female, or 'N' for Prefer not to say. "
        "If the input does not match these categories, return 'Invalid'. "
        "Do not return any other words or explanations.",
        user_input
    )
    gender_extracted = gender_extracted.strip().upper()
    
    if gender_extracted in {'M', 'F', 'N'}:
        return {
            'success': True,
            'value': gender_extracted,
            'status': 'complete'
        }
    
    return {
        'success': False,
        'value': 'Please specify Male, Female, or Prefer not to say.',
        'status': 'error'
    }

__all__ = ["get_gender"]
