from ..functions.doctor_details.extract_doctor_details import extract_doctor_details
from langchain.tools import Tool

def get_doctors_info(*args, **kwargs):
    """
    Fetch doctor details from the 'doctors' table.
    Extracts doctor details and formats the response accordingly.
    """
    try:
        # Get doctor details from the database
        input =args[0] if args else ""  

        doctor_details = extract_doctor_details(input)

        # If no doctor details are found
        if not doctor_details:
            return {
                "observation": "No doctor available in the database.",
                "action": "Error",
                "action_input": "No matching doctor found in the database."
            }

       
        # If details are found, return them
        return {
            "observation": f"Doctor details retrieved successfully'.",
            "action": "Final Answer",
            "action_input": doctor_details  # Returning the full details as a dictionary
        }

    except Exception as e:
        return {
            "observation": f"An error occurred: {str(e)}",
            "action": "Error",
            "action_input": "There was an issue retrieving doctor information. Please try again."
        }


# Define the tool as a LangChain Tool object
doctor_info_tool = Tool(
    name="Doctors Info",
    func=get_doctors_info,
    description="Fetch doctor details from the 'doctor_info_tool' table."
)

__all__ = ["doctor_info_tool"]
