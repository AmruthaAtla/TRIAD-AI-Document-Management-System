"""
General validation utilities.
"""
import re


def is_valid_email(email):
    """Validate email format."""
    if not email or "@" not in email:
        return False
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))
