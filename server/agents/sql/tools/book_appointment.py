from connection import supabase
from functions.Book_Appointment.extract_doctor_name import extract_doctor_name
from functions.Book_Appointment.extract_day_time import extract_day_time
from functions.Book_Appointment.extract_reason import extract_reason
from langchain.agents import Tool

# Function to book an appointment
def book_appointment(*args, **kwargs):
    """
    Handles the appointment booking process, including confirmation.
    """
    try:
        # Extract doctor name
        input =args[0] if args else ""  


        doctor_name = extract_doctor_name(input)
        
        print(f"Agent: You want to book an appointment with Dr. {doctor_name}.")

        # Extract doctor ID, appointment day, and time
        doctor_id, day, time = extract_day_time(doctor_name)

        if day and time:
            print(f"Agent: Your preferred appointment time is {day} at {time} with Doctor ID {doctor_id}.")
        else:
            print("Agent: Could not extract a valid appointment time.")
            return {
                "observation": "Invalid appointment time extracted.",
                "action": "Error",
                "action_input": "Unable to determine a valid appointment time. Please try again."
            }  

        # Extract reason for appointment
        reason = extract_reason()
        print(f"Agent: The reason for your appointment is {reason}.")

        # Confirm appointment
        while True:
            confirm = input("Agent: I have noted your appointment details. Would you like to confirm? (yes/no): ").strip().lower()
            
            if confirm == "yes":
                appointment_data = {
                    "appointment_id": 605960,
                    "patient_id": 10000032,
                    "doctor_id": doctor_id,
                    "reason": reason,
                    "appointment_day": day,
                    "appointment_time": time
                }

                # Insert into Supabase
                response = supabase.table("appointments").insert(appointment_data).execute()
                
                if response.data:
                    return {
                        "observation": f"Appointment with Dr. {doctor_name} confirmed for {day} at {time}.",
                        "action": "Final Answer",
                        "action_input": f"Your appointment has been successfully booked with Dr. {doctor_name} on {day} at {time}."
                    }
                else:
                    return {
                        "observation": f"Error while booking appointment: {response.error}",
                        "action": "Error",
                        "action_input": "There was an issue booking your appointment. Please try again."
                    }

            elif confirm == "no":
                return {
                    "observation": "User canceled the appointment booking.",
                    "action": "Abort",
                    "action_input": "Your appointment has not been confirmed. Let me know if you need any changes."
                }

            else:
                print("Agent: Invalid input. Please enter 'yes' or 'no'.")

    except Exception as e:
        return {
            "observation": f"An error occurred during the appointment booking process: {e}",
            "action": "Error",
            "action_input": "An internal error occurred. Please check the system."
        }

# Define the tool
book_appointment_tool = Tool(
    name="Book Appointment",
    func=book_appointment,
    description="Call this tool to book an appointment."
)

__all__ = ["book_appointment_tool"]
