
from ..functions.Register_Patient.get_anchor_year_group import get_anchor_year_group
from ..functions.Register_Patient.get_phoneNumber import get_phoneNumber
from ..functions.Register_Patient.get_address import get_address
from ..functions.Register_Patient.get_gender import get_gender
from ..functions.Register_Patient.get_name import get_name
from ..functions.Register_Patient.get_age import get_age
from langchain.agents import Tool
from ..connection import supabase
import random
import string

# Function to generate a unique 8-character patient ID
def generate_patient_id():
    return ''.join(random.choices(string.digits, k=8))

# Function to register a patient
def register_patient(*args, **kwargs):
    """
    Handles the patient registration process.
    """
    try:
        # Extract patient details
        patient_id = generate_patient_id()
        name = get_name()
        gender = get_gender()
        phone_number = get_phoneNumber()
        age = get_age()
        anchor_year_group = get_anchor_year_group(age)
        address = get_address()

        print(f"Agent: Registering patient {name} with ID {patient_id}")

        # Prepare patient data
        patient_data = {
            "patient_id": patient_id,
            "name": name,
            "gender": gender,
            "phone_number": phone_number,
            "age": age,
            "anchor_year_group": anchor_year_group,
            "address": address
        }

        # Insert into Supabase
        response = supabase.table("patients").insert(patient_data).execute()

        if response.data:
            observation = f"Patient {name} has been successfully registered with ID {patient_id}."
            return {
                "observation": observation,
                "action": "Final Answer",
                "action_input": f"You have been successfully registered with the ID {patient_id}."
            }
        else:
            observation = f"Error: Failed to register patient {name}. Supabase Error: {response.error}"
            return {
                "observation": observation,
                "action": "Error",
                "action_input": "There was an issue registering the patient. Please try again."
            }

    except Exception as e:
        observation = f"An error occurred during patient registration: {e}"
        return {
            "observation": observation,
            "action": "Error",
            "action_input": "An internal error occurred. Please check the system."
        }

# Define the tool
register_patient_tool = Tool(
    name="Register Patient",
    func=register_patient,
    description="Call this tool to register a patient with unique ID, name, gender, phone number, age, and address."
)

__all__ = ["register_patient_tool"]
