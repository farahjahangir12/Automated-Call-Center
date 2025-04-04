from ..connection import supabase
from ..functions.Cancel_Appointment.get_appointment_details import get_appointment_details
from ..functions.Cancel_Appointment.delete_appointment import delete_appointment
from ..functions.Cancel_Appointment.get_patient_name import get_patient_name
from langchain.agents import Tool

# Function to cancel an appointment
def cancel_appointment(*args, **kwargs):
    """
    Cancels a patient's appointment by fetching appointment details,
    confirming with the user using their name, and deleting it.
    """
    try:
        patient_id = input("Agent: Please enter your patient ID: ").strip()

        if not patient_id:
            return {
                "observation": "Patient ID cannot be empty.",
                "action": "Error",
                "action_input": "Please provide a valid patient ID."
            }

        # Fetch patient name
        patient_name = get_patient_name(patient_id)

        if not patient_name:
            return {
                "observation": "No patient found with this ID.",
                "action": "Error",
                "action_input": "Invalid patient ID. Please try again."
            }

        # Fetch appointment details
        appointment_details = get_appointment_details(patient_id)

        if not appointment_details:
            return {
                "observation": f"No appointment found for {patient_name}.",
                "action": "Error",
                "action_input": "No appointment exists under this ID."
            }

        # Confirmation message with patient's name
        confirmation = input(
            f"Agent: {patient_name}, are you sure you want to delete your appointment "
            f"with Dr. {appointment_details['doctor_name']} on {appointment_details['day']} at {appointment_details['time']}? (yes/no): "
        ).strip().lower()

        if confirmation != "yes":
            return {
                "observation": "Appointment cancellation aborted by the user.",
                "action": "Abort",
                "action_input": "Cancellation process stopped."
            }

        if delete_appointment(patient_id):
            return {
                "observation": f"Patient {patient_name}'s appointment has been successfully canceled.",
                "action": "Final Answer",
                "action_input": f"Your appointment has been successfully canceled, {patient_name}."
            }
        else:
            return {
                "observation": f"Error: Failed to cancel appointment for {patient_name}.",
                "action": "Error",
                "action_input": "There was an issue canceling the appointment. Please try again."
            }

    except Exception as e:
        return {
            "observation": f"An error occurred during appointment cancellation: {e}",
            "action": "Error",
            "action_input": "An internal error occurred. Please check the system."
        }

# Define the tool
cancel_appointment_tool = Tool(
    name="cancel Appointment",
    func=cancel_appointment,
    description="Call this tool to cancel a patient's appointment by providing their patient ID."
)

__all__ = ["cancel_appointment_tool"]
