# This file makes the appointmentSlots_info directory a Python package

# Explicit imports to avoid circular dependencies
from .get_available_slots import get_available_slots

__all__ = ['get_available_slots']
