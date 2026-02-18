"""
Utils package initialization
Provides utility functions for the application
"""

# Import all utility functions from submodules
from .auth import hash_password, verify_password
from .database import (
    load_pending_users,
    save_pending_users,
    load_password_reset_requests,
    save_password_reset_requests,
    load_email_config,
    save_email_config
)
from .validators import validate_email, validate_password, validate_username
from .email_handler import send_email

# Optional imports with error handling
try:
    from .helpers import *
except ImportError:
    pass

try:
    from .excel_handler import *
except ImportError:
    # Excel handler requires pandas, skip if not installed
    pass

try:
    from .backup_manager import *
except ImportError:
    pass

try:
    from .data_protection import *
except ImportError:
    pass

# Define what gets exported when using "from utils import *"
__all__ = [
    # Auth functions
    'hash_password',
    'verify_password',
    
    # Database functions
    'load_pending_users',
    'save_pending_users',
    'load_password_reset_requests',
    'save_password_reset_requests',
    'load_email_config',
    'save_email_config',
    
    # Validators
    'validate_email',
    'validate_password',
    'validate_username',
    
    # Email
    'send_email',
]