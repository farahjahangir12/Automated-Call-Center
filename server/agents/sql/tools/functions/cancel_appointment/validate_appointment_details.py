from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

async def validate_appointment_details(data: Dict) -> Dict:
    """
    Validate appointment details for cancellation
    
    Args:
        data (Dict): Dictionary containing appointment information
        
    Returns:
        Dict: Dictionary containing validation result
    """
    try:
        errors = []
        
        # Validate appointment ID
        if not data.get('appointment_id'):
            errors.append("Appointment ID is required")
        elif not data['appointment_id'].isdigit() or len(data['appointment_id']) != 8:
            errors.append("Invalid appointment ID format")
        
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
        logger.error(f"Error validating appointment details: {str(e)}")
        return {
            'success': False,
            'value': f"An error occurred while processing your request: {str(e)}",
            'confidence': 0.0
        }
