from agents.sql.tools.functions.book_appointment.extract_appointment_info import extract_appointment_info
from agents.sql.tools.functions.book_appointment.validate_appointment_info import validate_appointment_info
from agents.sql.tools.functions.book_appointment.create_appointment_record import create_appointment_record
from langchain.tools import StructuredTool
from typing import Dict, Any, Optional, Callable
import logging
from pydantic import BaseModel, Field
import asyncio

logger = logging.getLogger(__name__)

class AppointmentBookingInput(BaseModel):
    """Input schema for appointment booking"""
    input_data: str = Field(description="The user's input string")
    context: Optional[Dict] = Field(default_factory=dict, description="Additional context")

class AppointmentBookingTool:
    def __init__(
        self,
        doctor_info_tool: Callable,
        appointmentSlots_info_tool: Callable
    ):
        self.current_step = "get_doctor"
        self.collected_data = {}
        self.doctor_info_tool = doctor_info_tool
        self.appointmentSlots_info_tool = appointmentSlots_info_tool

    async def invoke(self, input_data: str, context: Dict = None) -> Dict:
        """Main entry point that matches LangChain's expected interface"""
        if isinstance(input_data, dict):
            input_data = input_data.get("input_data", "")
        
        if context is None:
            context = {}
        
        # Ensure we have a proper dictionary for context
        if not isinstance(context, dict):
            context = {}
        
        # Create a new instance for each invocation to avoid state issues
        tool_instance = AppointmentBookingTool(
            doctor_info_tool=self.doctor_info_tool,
            appointmentSlots_info_tool=self.appointmentSlots_info_tool
        )
        return await tool_instance.handle_query(input_data, context)

    async def handle_query(self, input_str: str, context: Dict[str, Any]) -> Dict:
        """
        Handles interactive appointment booking.
        Returns dict with:
        - response: string for user
        - current_step: next step identifier
        - collected_data: updated context
        - status: 'in_progress'|'complete'|'error'
        """
        self.current_step = context.get('current_step', 'get_doctor')
        self.collected_data = context.get('collected_data', {})

        try:
            if self.current_step == 'get_doctor':
                # First step - ask for doctor if not specified
                if not input_str.strip():
                    return {
                        'response': "Which doctor would you like to see? Please specify their name.",
                        'current_step': 'get_doctor',
                        'collected_data': {},
                        'status': 'in_progress'
                    }
                
                # Extract doctor information
                doctor_info = await extract_appointment_info(input_str, field_type="doctor_name")
                
                if doctor_info.get('success', False):
                    # Use doctor_info_tool to get full doctor details
                    doctor_details = await self.doctor_info_tool.invoke(input_str)
                    if doctor_details.get('success', False):
                        self.collected_data['doctor'] = doctor_details
                        self.current_step = 'get_time'
                        return {
                            'response': f"Great! You've selected {doctor_details['value']}. When would you like to schedule your appointment?",
                            'current_step': 'get_time',
                            'collected_data': self.collected_data,
                            'status': 'in_progress'
                        }
                    else:
                        return {
                            'response': f"I couldn't find details for the doctor you specified. Please try again.",
                            'current_step': 'get_doctor',
                            'collected_data': {},
                            'status': 'in_progress'
                        }
                else:
                    return {
                        'response': f"I couldn't understand the doctor you specified. Please try again.",
                        'current_step': 'get_doctor',
                        'collected_data': {},
                        'status': 'in_progress'
                    }

            elif self.current_step == 'get_time':
                # Second step - ask for time if not specified
                if not input_str.strip():
                    return {
                        'response': "When would you like to schedule your appointment? Please specify a date and time.",
                        'current_step': 'get_time',
                        'collected_data': self.collected_data,
                        'status': 'in_progress'
                    }
                
                # Extract time information
                time_info = await extract_appointment_info(input_str, field_type="day_time")
                
                if time_info.get('success', False):
                    # Check if time slot is available
                    slot_check = await self.appointmentSlots_info_tool.invoke(
                        {
                            'doctor_id': self.collected_data['doctor']['id'],
                            'time': time_info['value']
                        }
                    )
                    
                    if slot_check.get('success', False):
                        self.collected_data['time'] = time_info
                        self.current_step = 'confirm'
                        return {
                            'response': f"The time {time_info['value']} is available. Would you like to confirm this appointment? (yes/no)",
                            'current_step': 'confirm',
                            'collected_data': self.collected_data,
                            'status': 'in_progress'
                        }
                    else:
                        # Get list of available slots
                        slots = await self.appointmentSlots_info_tool.invoke(
                            {
                                'doctor_id': self.collected_data['doctor']['id']
                            }
                        )
                        if slots.get('success', False):
                            return {
                                'response': f"I'm sorry, that time is not available. Available slots: {slots['value']}. Please choose another time.",
                                'current_step': 'get_time',
                                'collected_data': self.collected_data,
                                'status': 'in_progress'
                            }
                        else:
                            return {
                                'response': f"I couldn't check available slots. Please try a different time.",
                                'current_step': 'get_time',
                                'collected_data': self.collected_data,
                                'status': 'in_progress'
                            }
                else:
                    return {
                        'response': f"I couldn't understand the time you provided. Please specify a valid time (e.g., 2:30pm).",
                        'current_step': 'get_time',
                        'collected_data': self.collected_data,
                        'status': 'in_progress'
                    }

            elif self.current_step == 'confirm':
                # Third step - confirm appointment
                if input_str.lower() == 'yes':
                    # Create appointment record
                    result = await create_appointment_record(self.collected_data)
                    if result.get('success', False):
                        return {
                            'response': f"Your appointment has been successfully booked! {result['value']}",
                            'current_step': 'get_doctor',
                            'collected_data': {},
                            'status': 'complete'
                        }
                    else:
                        return {
                            'response': f"Sorry, we couldn't book your appointment: {result['value']}",
                            'current_step': 'get_doctor',
                            'collected_data': {},
                            'status': 'error'
                        }
                else:
                    return {
                        'response': "Appointment not confirmed. How can I assist you further?",
                        'current_step': 'get_doctor',
                        'collected_data': {},
                        'status': 'in_progress'
                    }

        except Exception as e:
            logger.error(f"Error in handle_query: {str(e)}")
            return {
                'response': f'Error: {str(e)}',
                'current_step': 'get_doctor',
                'collected_data': {},
                'status': 'error'
            }

# Create tool instance
book_appointment_tool = StructuredTool.from_function(
    lambda input_data, context: asyncio.run(AppointmentBookingTool(
        doctor_info_tool=doctor_info_tool,
        appointmentSlots_info_tool=appointmentSlots_info_tool
    ).invoke(input_data, context)),
    name="book_appointment_tool",
    description="Handle appointment booking requests. This tool manages the entire booking process interactively, guiding the user through selecting a doctor, checking availability, and confirming the appointment.",
    args_schema=AppointmentBookingInput
)