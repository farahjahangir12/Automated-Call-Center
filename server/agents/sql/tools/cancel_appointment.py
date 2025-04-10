from agents.sql.tools.functions.cancel_appointment.extract_appointment_details import extract_appointment_details
from agents.sql.tools.functions.cancel_appointment.validate_appointment_details import validate_appointment_details
from agents.sql.tools.functions.cancel_appointment.delete_appointment_record import delete_appointment_record
from langchain.tools import Tool
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class AppointmentCancellationTool:
    def __init__(self):
        self.current_step = "get_patient_id"
        self.collected_data = {}

    async def invoke(self, input_data: Dict) -> Dict:
        """Main entry point that matches LangChain's expected interface"""
        return await self.handle_query(
            input_data.get("input_str", ""),
            input_data.get("context", {})
        )

    async def handle_query(self, input_str: str, context: Dict[str, Any]) -> Dict:
        """
        Handles the appointment cancellation process.
        Returns dict with:
        - response: string for user
        - current_step: next step identifier
        - collected_data: updated context
        - status: 'in_progress'|'complete'|'error'
        """
        self.current_step = context.get('current_step', 'get_patient_id')
        self.collected_data = context.get('collected_data', {})

        try:
            if self.current_step == 'get_patient_id':
                return await self._handle_patient_id_step(input_str)
            elif self.current_step == 'confirm_cancellation':
                return await self._handle_confirmation_step(input_str)
            else:
                return self._reset_flow("Let's start over. Please provide your patient ID.")
                
        except Exception as e:
            logger.error(f"Cancellation error: {str(e)}")
            return self._reset_flow("I encountered an error. Let's start over.")

    async def _handle_patient_id_step(self, input_str: str) -> Dict:
        """Handle patient ID input step"""
        if not input_str.strip():
            return {
                'response': "Please provide your patient ID.",
                'current_step': 'get_patient_id',
                'collected_data': self.collected_data,
                'status': 'in_progress'
            }

        # Get patient name
        name_result = get_patient_name(input_str)
        if not name_result['success']:
            return {
                'response': name_result['value'],
                'current_step': 'get_patient_id',
                'collected_data': self.collected_data,
                'status': 'in_progress'
            }

        # Get appointment details
        details_result = get_appointment_details(input_str)
        if not details_result['success']:
            return {
                'response': details_result['value'],
                'current_step': 'get_patient_id',
                'collected_data': self.collected_data,
                'status': 'in_progress'
            }

        # Store data and ask for confirmation
        self.collected_data.update({
            'patient_id': input_str,
            'patient_name': name_result['value'],
            'appointment_details': details_result['value']
        })

        details = details_result['value']
        return {
            'response': f"{name_result['value']}, are you sure you want to cancel your appointment "
                      f"with Dr. {details['doctor_name']} on {details['day']} at {details['time']}? (yes/no)",
            'current_step': 'confirm_cancellation',
            'collected_data': self.collected_data,
            'status': 'in_progress'
        }

    async def _handle_confirmation_step(self, input_str: str) -> Dict:
        """Handle confirmation step"""
        if input_str.lower() not in ['yes', 'y']:
            return self._reset_flow("Cancellation aborted. Let's start over if you want to try again.")

        try:
            result = delete_appointment(self.collected_data['patient_id'])
            if not result['success']:
                return {
                    'response': result['value'],
                    'current_step': 'get_patient_id',
                    'collected_data': {},
                    'status': 'error'
                }

            return {
                'response': f"Your appointment has been successfully canceled, {self.collected_data['patient_name']}.",
                'current_step': 'complete',
                'collected_data': {},
                'status': 'complete'
            }

        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            return {
                'response': "Sorry, I couldn't cancel your appointment. Please try again.",
                'current_step': 'get_patient_id',
                'collected_data': {},
                'status': 'error'
            }

    def _reset_flow(self, message: str) -> Dict:
        """Reset the cancellation flow"""
        self.current_step = 'get_patient_id'
        self.collected_data = {}
        return {
            'response': message,
            'current_step': 'get_patient_id',
            'collected_data': {},
            'status': 'in_progress'
        }

# Create tool instance
cancellation_tool = AppointmentCancellationTool()

# LangChain tool decorator
cancel_appointment_tool = Tool(
    name="Cancel Appointment",
    func=cancellation_tool.invoke,
    description="Cancel a patient's appointment by providing their patient ID."
)

__all__ = ["cancel_appointment_tool"]
