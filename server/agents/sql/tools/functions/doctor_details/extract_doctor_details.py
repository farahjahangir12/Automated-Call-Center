import re
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def extract_doctor_details(text: str) -> Dict:
    """
    Extract doctor details from user input
    
    Args:
        text (str): User input containing doctor information
        
    Returns:
        Dict: Dictionary containing extracted doctor information
    """
    try:
        # Basic pattern matching for doctor names
        doctor_pattern = r"(dr\.|doctor)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)"
        match = re.search(doctor_pattern, text, re.IGNORECASE)
        
        if match:
            doctor_name = match.group(2).strip()
            return {
                'success': True,
                'value': doctor_name,
                'confidence': 0.9
            }
        else:
            return {
                'success': False,
                'value': "I couldn't find a doctor's name in your message.",
                'confidence': 0.1
            }
    except Exception as e:
        logger.error(f"Error extracting doctor details: {str(e)}")
        return {
            'success': False,
            'value': f"An error occurred while processing your request: {str(e)}",
            'confidence': 0.0
        }
