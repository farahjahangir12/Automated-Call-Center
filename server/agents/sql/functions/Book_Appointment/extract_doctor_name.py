from ...functions.find_best_match import find_best_match
from ...functions.create_prompt import create_prompt

async def extract_doctor_name(user_input: str) -> dict:
    """
    Extracts and validates a doctor's name from the given input.
    Args:
        user_input: String containing the potential doctor's name
    Returns:
        dict: {
            'success': bool,
            'value': str,  # doctor's name if found, error message if not
            'status': str  # 'complete' or 'error'
        }
    """
    if not user_input:
        return {
            'success': False,
            'value': 'Please provide a doctor\'s name.',
            'status': 'error'
        }
    
    # Extract only the name
    name_extracted = await create_prompt(
        "Extract only the doctor's name from the given input. "
        "Ensure that the response contains only a valid human-like name and not a sentence, "
        "random text, or unrelated words. "
        "If the input contains a valid name, return only the name. "
        "If the input contains unrelated text, a script, or random words, respond with 'Not a valid name.' "
        "Do not include explanations, extra words, or any text other than the extracted name or rejection message.",
        user_input
    )
    name_extracted = name_extracted.strip()

    # Check for best match in database
    doctor_name = await find_best_match(name_extracted)

    if doctor_name:
        return {
            'success': True,
            'value': doctor_name,
            'status': 'complete'
        }
    
    return {
        'success': False,
        'value': 'Sorry, this doctor is not available. Please provide a valid doctor\'s name.',
        'status': 'error'
    }

__all__ = ["extract_doctor_name"]