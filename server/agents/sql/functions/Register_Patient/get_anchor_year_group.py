from datetime import datetime

def get_anchor_year_group(age: int) -> int:
    """
    Calculate the year of birth based on the given age.
    
    :param age: The age of the person.
    :return: The year of birth.
    """
    if not isinstance(age, int) or age <= 0:
        raise ValueError("Age must be a positive integer.")

    current_year = datetime.now().year
    year_of_birth = current_year - age
    return year_of_birth

__all__ = ["get_anchor_year_group"]
