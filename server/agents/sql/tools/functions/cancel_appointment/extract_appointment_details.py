import re
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

async def extract_appointment_details(text: str) -> Dict:
    """
    Extract appointment details for cancellation
    
    Args:
        text (str): User input containing appointment information
        
    Returns:
        Dict: Dictionary containing extracted information
    """
    try:
        # Extract appointment ID
        id_pattern = r"#\d{8}"
        match = re.search(id_pattern, text)
        if match:
            return {
                'success': True,
                'value': match.group(0)[1:],  # Remove the #
                'confidence': 0.9
            }
        
        return {
            'success': False,
            'value': "Please provide a valid appointment ID (e.g., #12345678).",
            'confidence': 0.1
        }
        
    except Exception as e:
        logger.error(f"Error extracting appointment details: {str(e)}")
        return {
            'success': False,
            'value': f"An error occurred while processing your request: {str(e)}",
            'confidence': 0.0
        }
