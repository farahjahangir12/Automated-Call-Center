from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

async def validate_appointment_info(data: Dict) -> Dict:
    """
    Validate appointment information
    
    Args:
        data (Dict): Dictionary containing appointment information
        
    Returns:
        Dict: Dictionary containing validation result
    """
    try:
        errors = []
        
        # Validate doctor name
        if not data.get('doctor_name'):
            errors.append("Doctor's name is required")
        
        # Validate time
        if not data.get('appointment_time'):
            errors.append("Appointment time is required")
        
        # Validate reason
        if not data.get('reason'):
            errors.append("Reason for appointment is required")
        
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
        logger.error(f"Error validating appointment info: {str(e)}")
        return {
            'success': False,
            'value': f"An error occurred while processing your request: {str(e)}",
            'confidence': 0.0
        }
