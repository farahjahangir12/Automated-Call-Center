from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

async def validate_patient_info(data: Dict) -> Dict:
    """
    Validate patient information
    
    Args:
        data (Dict): Dictionary containing patient information
        
    Returns:
        Dict: Dictionary containing validation result
    """
    try:
        errors = []
        
        # Validate name
        if not data.get('name'):
            errors.append("Name is required")
        
        # Validate gender
        if data.get('gender') not in ['male', 'female', 'other']:
            errors.append("Invalid gender")
        
        # Validate phone number
        if not data.get('phone_number'):
            errors.append("Phone number is required")
        
        # Validate address
        if not data.get('address'):
            errors.append("Address is required")
        
        if errors:
            return {
                'success': False,
                'value': "\n".join(errors),
                'confidence': 0.1
            }
            
        return {
            'success': True,
            'value': "All information is valid",
            'confidence': 1.0
        }
        
    except Exception as e:
        logger.error(f"Error validating patient info: {str(e)}")
        return {
            'success': False,
            'value': f"An error occurred while processing your request: {str(e)}",
            'confidence': 0.0
        }
