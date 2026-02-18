"""
Authentication utilities
"""
import hashlib


def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed_password

def get_current_user_flask(session_obj) -> str:
    """Get current logged-in user (Flask version)"""
    user = session_obj.get('user', {})
    return user.get('username', '')

def get_current_role_flask(session_obj) -> str:
    """Get current user role (Flask version)"""
    user = session_obj.get('user', {})
    return user.get('role', '')

def is_audit_reviewer_flask(session_obj) -> bool:
    """Check if current user is audit reviewer (Flask version)"""
    user = session_obj.get('user', {})
    return user.get('is_audit_reviewer', False)