from agents.sql.tools.functions.register_patient.extract_patient_info import extract_patient_info
from agents.sql.tools.functions.register_patient.validate_patient_info import validate_patient_info
from agents.sql.tools.functions.register_patient.create_patient_record import create_patient_record
from langchain.tools import StructuredTool
from typing import Dict, Any, Optional
from pydantic import BaseModel
import random
import string
import logging

logger = logging.getLogger(__name__)

class PatientRegistrationTool:
    def __init__(self):
        self.current_step = "get_name"
        self.collected_data = {}

    async def invoke(self, input_data: str | Dict, context: Dict = None) -> Dict:
        """Main entry point that matches LangChain's expected interface"""
        try:
            # Handle both structured and direct input
            if isinstance(input_data, dict):
                query = input_data.get('input_data', '')
                ctx = input_data.get('context', {}) or context or {}
            else:
                query = input_data
                ctx = context or {}

            # Ensure we await the handle_query call
            result = await self.handle_query(query, ctx)
            return result
        except Exception as e:
            logger.error(f"Error in registration tool invoke: {str(e)}")
            return {
                "response": f"Registration error: {str(e)}. Please try again.",
                "status": "error"
            }

    async def handle_query(self, input_str: str, context: Dict[str, Any]) -> Dict:
        """
        Handles the patient registration process.
        Returns dict with:
        - response: string for user
        - current_step: next step identifier
        - collected_data: updated context
        - status: 'in_progress'|'complete'|'error'
        """
        self.current_step = context.get('current_step', 'get_name')
        self.collected_data = context.get('collected_data', {})

        try:
            if self.current_step == 'get_name':
                return await self._handle_name_step(input_str)
            elif self.current_step == 'get_gender':
                return await self._handle_gender_step(input_str)
            elif self.current_step == 'get_phone':
                return await self._handle_phone_step(input_str)
            elif self.current_step == 'get_age':
                return await self._handle_age_step(input_str)
            elif self.current_step == 'get_address':
                return await self._handle_address_step(input_str)
            elif self.current_step == 'confirm':
                return await self._handle_confirmation_step(input_str)
            else:
                return self._reset_flow("Let's start your registration. What is your name?")
                
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return self._reset_flow("I encountered an error. Let's start over.")

    async def _handle_name_step(self, input_str: str) -> Dict:
        """Handle name input step"""
        try:
            result = await extract_patient_info(input_str, 'name')
            
            if not result['success']:
                return {
                    'response': result['value'],
                    'current_step': 'get_name',
                    'collected_data': self.collected_data,
                    'status': 'in_progress'
                }
            
            self.collected_data['name'] = result['value']
            return {
                'response': "What is your gender? (Male/Female/Prefer not to say)",
                'current_step': 'get_gender',
                'collected_data': self.collected_data,
                'status': 'in_progress'
            }
        except Exception as e:
            logger.error(f"Error in name step: {e}")
            return self._reset_flow("I encountered an error. Let's start over with your name.")

    async def _handle_gender_step(self, input_str: str) -> Dict:
        """Handle gender input step"""
        try:
            result = await extract_patient_info(input_str, 'gender')
            
            if not result['success']:
                return {
                    'response': result['value'],
                    'current_step': 'get_gender',
                    'collected_data': self.collected_data,
                    'status': 'in_progress'
                }
            
            self.collected_data['gender'] = result['value']
            return {
                'response': "What is your phone number?",
                'current_step': 'get_phone',
                'collected_data': self.collected_data,
                'status': 'in_progress'
            }
        except Exception as e:
            logger.error(f"Error in gender step: {e}")
            return self._reset_flow("I encountered an error. Let's start over with your gender.")

    async def _handle_phone_step(self, input_str: str) -> Dict:
        """Handle phone number input step"""
        try:
            result = await extract_patient_info(input_str, 'phone_number')
            
            if not result['success']:
                return {
                    'response': result['value'],
                    'current_step': 'get_phone',
                    'collected_data': self.collected_data,
                    'status': 'in_progress'
                }
            
            self.collected_data['phone_number'] = result['value']
            return {
                'response': "What is your age?",
                'current_step': 'get_age',
                'collected_data': self.collected_data,
                'status': 'in_progress'
            }
        except Exception as e:
            logger.error(f"Error in phone step: {e}")
            return self._reset_flow("I encountered an error. Let's start over with your phone number.")

    async def _handle_age_step(self, input_str: str) -> Dict:
        """Handle age input step"""
        try:
            result = await extract_patient_info(input_str, 'age')
            
            if not result['success']:
                return {
                    'response': result['value'],
                    'current_step': 'get_age',
                    'collected_data': self.collected_data,
                    'status': 'in_progress'
                }
            
            self.collected_data['age'] = result['value']
            return {
                'response': "What is your address?",
                'current_step': 'get_address',
                'collected_data': self.collected_data,
                'status': 'in_progress'
            }
        except Exception as e:
            logger.error(f"Error in age step: {e}")
            return self._reset_flow("I encountered an error. Let's start over with your age.")

    async def _handle_address_step(self, input_str: str) -> Dict:
        """Handle address input step"""
        try:
            result = await extract_patient_info(input_str, 'address')
            
            if not result['success']:
                return {
                    'response': result['value'],
                    'current_step': 'get_address',
                    'collected_data': self.collected_data,
                    'status': 'in_progress'
                }
            
            self.collected_data['address'] = result['value']
            return {
                'response': f"Please confirm your details:\n" +
                          f"Name: {self.collected_data['name']}\n" +
                          f"Gender: {self.collected_data['gender']}\n" +
                          f"Phone: {self.collected_data['phone_number']}\n" +
                          f"Age: {self.collected_data['age']}\n" +
                          f"Address: {self.collected_data['address']}\n\n" +
                          f"Is this correct? (yes/no)",
                'current_step': 'confirm',
                'collected_data': self.collected_data,
                'status': 'in_progress'
            }
        except Exception as e:
            logger.error(f"Error in address step: {e}")
            return self._reset_flow("I encountered an error. Let's start over with your address.")

    async def _handle_confirmation_step(self, input_str: str) -> Dict:
        """Handle final confirmation and registration"""
        if input_str.lower() not in ['yes', 'y']:
            return self._reset_flow("Let's start over. What is your name?")
        
        try:
            # Validate patient data
            validation_result = await validate_patient_info(self.collected_data)
            if not validation_result['success']:
                return {
                    'response': validation_result['value'],
                    'current_step': 'get_name',
                    'collected_data': {},
                    'status': 'error'
                }
            
            # Create patient record
            result = await create_patient_record(self.collected_data)
            if not result['success']:
                return {
                    'response': result['value'],
                    'current_step': 'get_name',
                    'collected_data': {},
                    'status': 'error'
                }
            
            return {
                'response': f"Great! You have been successfully registered with ID {result['value']}.",
                'current_step': 'complete',
                'collected_data': {},
                'status': 'complete'
            }
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            return {
                'response': "Sorry, I couldn't complete your registration. Please try again.",
                'current_step': 'get_name',
                'collected_data': {},
                'status': 'error'
            }

    def _reset_flow(self, message: str) -> Dict:
        """Reset the registration flow"""
        self.current_step = 'get_name'
        self.collected_data = {}
        return {
            'response': message,
            'current_step': 'get_name',
            'collected_data': {},
            'status': 'in_progress'
        }

async def create_patient_record(data: Dict) -> Dict:
    """
    Create a new patient record in the database
    """
    try:
        # Generate patient ID
        patient_id = ''.join(random.choices(string.digits, k=8))
        
        # Prepare patient data
        patient_data = {
            "patient_id": patient_id,
            **data
        }
        
        # Insert into database
        result = await supabase.query("patients", "insert", patient_data)
        
        if not result:
            raise Exception("Failed to save patient data")
        
        return {
            'success': True,
            'value': patient_id,
            'confidence': 1.0
        }
        
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        return {
            'success': False,
            'value': f"Failed to create patient record: {str(e)}",
            'confidence': 0.0
        }

# Input schema for registration
class PatientRegistrationInput(BaseModel):
    input_data: str
    context: Optional[Dict] = {}

# Create tool instance
registration_tool = PatientRegistrationTool()

# LangChain tool decorator
register_patient_tool = StructuredTool(
    name="Register Patient",
    func=registration_tool.invoke,
    description="Register a new patient by providing their details (name, gender, phone, age, address).",
    args_schema=PatientRegistrationInput,
    is_async=True
)

__all__ = ["register_patient_tool"]
