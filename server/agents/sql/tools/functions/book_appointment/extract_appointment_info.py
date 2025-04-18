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
            # First try with dr/doctor prefix
            doctor_pattern = r"(?:dr\.|doctor)?\s*([a-zA-Z]+(?:\s+[a-zA-Z]+)*)"
            match = re.search(doctor_pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Ensure we have at least two words (first and last name)
                if len(name.split()) >= 2:
                    return {
                        'success': True,
                        'value': name,
                        'confidence': 0.9
                    }
            return {
                'success': False,
                'value': "Please provide a valid doctor's full name (first and last name).",
                'confidence': 0.1
            }
            
        elif field_type == 'day_time':
            # Extract day and time
            # Handle various time formats
            time_pattern = r"(?:\d{1,2})(?::|\.)?(\d{2})?\s*(?:am|pm|AM|PM)?"
            match = re.search(time_pattern, text, re.IGNORECASE)
            if match:
                time_str = match.group(0).strip()
                # Convert to 24-hour format if needed
                try:
                    # If minutes not provided, add :00
                    if ':' not in time_str and '.' not in time_str:
                        time_str = f"{time_str}:00"
                    # Replace dot with colon if used
                    time_str = time_str.replace('.', ':')
                    return {
                        'success': True,
                        'value': time_str,
                        'confidence': 0.9
                    }
                except ValueError:
                    pass
            return {
                'success': False,
                'value': "Please provide a valid time (e.g., 2:30pm or 14:30).",
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
