import uuid
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

async def create_appointment_record(data: Dict) -> Dict:
    """
    Create a new appointment record
    
    Args:
        data (Dict): Dictionary containing appointment information
        
    Returns:
        Dict: Dictionary containing appointment details
    """
    try:
        # Generate appointment ID
        appointment_id = str(uuid.uuid4())
        
        # Create appointment data
        appointment = {
            'appointment_id': appointment_id,
            'doctor_name': data['doctor_name'],
            'appointment_time': data['appointment_time'],
            'reason': data['reason'],
            'status': 'scheduled'
        }
        
        # Log the creation
        logger.info(f"Created appointment: {appointment}")
        
        return appointment
        
    except Exception as e:
        logger.error(f"Error creating appointment: {str(e)}")
        raise
