import re
from ...functions.create_prompt import create_prompt

async def get_age(user_input: str) -> dict:
    """
    Extract and validate age from the given input.
    Args:
        user_input: String containing the potential age
    Returns:
        dict: {
            'success': bool,
            'value': int or str,  # age if valid, error message if not
            'status': str  # 'complete' or 'error'
        }
    """
    if not user_input or not any(char.isdigit() for char in user_input):
        return {
            'success': False,
            'value': 'Please provide a valid number for age.',
            'status': 'error'
        }
    
    # Extract age using LLM
    age_extracted = await create_prompt(
        "Extract the numeric age from the input. "
        "Return only the number without any explanations, context, or additional text. "
        "Do NOT include any reasoning, interpretations, or words—ONLY the number.",
        user_input
    )
    age_extracted = age_extracted.strip()
    
    # Extract numbers from the result
    extracted_numbers = re.findall(r"\d+", age_extracted)
    if not extracted_numbers:
        return {
            'success': False,
            'value': 'Please provide a valid age.',
            'status': 'error'
        }
    
    age = int(extracted_numbers[0])
    if 1 <= age <= 100:
        return {
            'success': True,
            'value': age,
            'status': 'complete'
        }
    
    return {
        'success': False,
        'value': 'Age must be between 1 and 100. Please provide a valid age.',
        'status': 'error'
    }

__all__ = ["get_age"]
