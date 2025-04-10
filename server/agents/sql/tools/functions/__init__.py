# This file makes the functions directory a Python package

# Lazy imports to avoid circular dependencies
__all__ = [
    'doctor_details',
    'register_patient',
    'book_appointment',
    'appointmentSlots_info',
    'cancel_appointment'
]

def __getattr__(name):
    if name == 'doctor_details':
        from .doctor_details.extract_doctor_details import extract_doctor_details
        return extract_doctor_details
    elif name == 'register_patient':
        from .register_patient import (
            extract_patient_info,
            validate_patient_info,
            create_patient_record
        )
        return {
            'extract_patient_info': extract_patient_info,
            'validate_patient_info': validate_patient_info,
            'create_patient_record': create_patient_record
        }
    elif name == 'book_appointment':
        from .book_appointment import (
            extract_appointment_info,
            validate_appointment_info,
            create_appointment_record
        )
        return {
            'extract_appointment_info': extract_appointment_info,
            'validate_appointment_info': validate_appointment_info,
            'create_appointment_record': create_appointment_record
        }
    elif name == 'appointmentSlots_info':
        from .appointmentSlots_info.get_available_slots import get_available_slots
        return get_available_slots
    elif name == 'cancel_appointment':
        from .cancel_appointment import (
            extract_appointment_details,
            validate_appointment_details,
            delete_appointment_record
        )
        return {
            'extract_appointment_details': extract_appointment_details,
            'validate_appointment_details': validate_appointment_details,
            'delete_appointment_record': delete_appointment_record
        }
    raise AttributeError(f"module {__name__} has no attribute {name}")
