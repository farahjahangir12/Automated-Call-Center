import re
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

async def extract_appointment_info(text: str, field_type: str = None) -> Dict:
    """
    Extract appointment information based on field type
    
    Args:
        text (str): User input containing appointment information
        field_type (str): Type of information to extract (doctor_name, day_time, reason)
        
    Returns:
        Dict: Dictionary containing extracted information
    """
    try:
        if field_type == 'doctor_name':
            # Extract doctor name
            doctor_pattern = r"(dr\.|doctor)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)"
            match = re.search(doctor_pattern, text, re.IGNORECASE)
            if match:
                return {
                    'success': True,
                    'value': match.group(2).strip(),
                    'confidence': 0.9
                }
            return {
                'success': False,
                'value': "Please provide a valid doctor's name.",
                'confidence': 0.1
            }
            
        elif field_type == 'day_time':
            # Extract day and time
            # This is a simplified example - in production you'd want more robust date/time parsing
            time_pattern = r"(?:\d{1,2}:\d{2})\s*(?:am|pm)?"
            match = re.search(time_pattern, text, re.IGNORECASE)
            if match:
                return {
                    'success': True,
                    'value': match.group(0).strip(),
                    'confidence': 0.9
                }
            return {
                'success': False,
                'value': "Please provide a valid time (e.g., 2:30pm).",
                'confidence': 0.1
            }
            
        elif field_type == 'reason':
            # Extract reason
            reason = text.strip()
            if not reason:
                return {
                    'success': False,
                    'value': "Please provide a reason for the appointment.",
                    'confidence': 0.1
                }
            return {
                'success': True,
                'value': reason,
                'confidence': 0.9
            }
            
        return {
            'success': False,
            'value': f"Unknown field type: {field_type}",
            'confidence': 0.0
        }
        
    except Exception as e:
        logger.error(f"Error extracting appointment info: {str(e)}")
        return {
            'success': False,
            'value': f"An error occurred while processing your request: {str(e)}",
            'confidence': 0.0
        }
