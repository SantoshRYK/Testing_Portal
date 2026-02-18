"""
Validation utilities
"""
import re
from typing import Tuple, Optional


def validate_username(username: str) -> Tuple[bool, str]:
    """
    Validate username
    Returns: (is_valid, error_message)
    """
    if not username:
        return False, "Username is required"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    if len(username) > 50:
        return False, "Username must be less than 50 characters"
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    
    return True, ""


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email address
    Returns: (is_valid, error_message)
    """
    if not email:
        return False, "Email is required"
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    return True, ""


def validate_password(password: str, confirm_password: Optional[str] = None) -> Tuple[bool, str]:
    """
    Validate password
    Returns: (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    # Only check confirmation if it's provided (not None)
    if confirm_password is not None and password != confirm_password:
        return False, "Passwords do not match"
    
    return True, ""