import re
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

async def extract_patient_info(text: str, field_type: str) -> Dict:
    """
    Extract patient information based on field type
    
    Args:
        text (str): User input containing patient information
        field_type (str): Type of information to extract (name, gender, phone_number, address)
        
    Returns:
        Dict: Dictionary containing extracted information
    """
    try:
        if field_type == 'name':
            # Extract name
            name = text.strip()
            if not name:
                return {
                    'success': False,
                    'value': "Please provide a valid name.",
                    'confidence': 0.1
                }
            return {
                'success': True,
                'value': name,
                'confidence': 0.9
            }
        
        elif field_type == 'gender':
            # Extract gender
            gender = text.lower()
            valid_genders = ['male', 'female', 'other']
            if gender not in valid_genders:
                return {
                    'success': False,
                    'value': "Please provide a valid gender (male, female, or other).",
                    'confidence': 0.1
                }
            return {
                'success': True,
                'value': gender,
                'confidence': 0.9
            }
        
        elif field_type == 'phone_number':
            # Extract phone number
            phone_pattern = r'\+?\d{10,15}'
            match = re.search(phone_pattern, text)
            if not match:
                return {
                    'success': False,
                    'value': "Please provide a valid phone number.",
                    'confidence': 0.1
                }
            return {
                'success': True,
                'value': match.group(0),
                'confidence': 0.9
            }
        
        elif field_type == 'address':
            # Extract address
            address = text.strip()
            if not address:
                return {
                    'success': False,
                    'value': "Please provide a valid address.",
                    'confidence': 0.1
                }
            return {
                'success': True,
                'value': address,
                'confidence': 0.9
            }
        
        return {
            'success': False,
            'value': f"Unknown field type: {field_type}",
            'confidence': 0.0
        }
        
    except Exception as e:
        logger.error(f"Error extracting patient info: {str(e)}")
        return {
            'success': False,
            'value': f"An error occurred while processing your request: {str(e)}",
            'confidence': 0.0
        }
