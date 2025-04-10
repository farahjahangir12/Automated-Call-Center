# This file makes the doctor_details directory a Python package

# Explicit imports to avoid circular dependencies
from .extract_doctor_details import extract_doctor_details

__all__ = ['extract_doctor_details']
