# config.py
"""
Application configuration and constants
Centralized configuration for easy management
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==================== PATHS ====================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = os.path.join(BASE_DIR, "data")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Data file paths
USERS_FILE = os.path.join(DATA_DIR, "users.json")
ALLOCATIONS_FILE = os.path.join(DATA_DIR, "allocations.json")
UAT_RECORDS_FILE = os.path.join(DATA_DIR, "uat_records.json")
AUDIT_LOGS_FILE = os.path.join(DATA_DIR, "audit_logs.json")
EMAIL_CONFIG_FILE = os.path.join(DATA_DIR, "email_config.json")
PENDING_USERS_FILE = os.path.join(DATA_DIR, "pending_users.json")
PASSWORD_RESET_FILE = os.path.join(DATA_DIR, "password_reset_requests.json")
TRAIL_DOCUMENTS_FILE = os.path.join(DATA_DIR, "trail_documents.json")
CHANGE_REQUESTS_FILE = os.path.join(DATA_DIR, "change_requests.json")
QUALITY_RECORDS_FILE = os.path.join(DATA_DIR, "quality_records.json")

# ==================== APP SETTINGS ====================
APP_TITLE = "Test Engineer Portal"
APP_ICON = "🧪"
PAGE_LAYOUT = "wide"

# ==================== DEFAULT CREDENTIALS ====================
DEFAULT_SUPERUSER = {
    "username": "superuser",
    "password": "super123",  # Will be hashed
    "email": "superuser@testportal.com",
    "role": "superuser"
}

# ==================== ROLES ====================
ROLES = {
    "superuser": {
        "name": "Super User", 
        "emoji": "👑", 
        "level": 5,
        "permissions": ["all"]
    },
    "cdp": {
        "name": "CDP", 
        "emoji": "📊", 
        "level": 4,
        "permissions": ["change_request_full"]
    },
    "manager": {
        "name": "Manager", 
        "emoji": "👨‍💼", 
        "level": 3,
        "permissions": ["view_all", "change_request_view", "download"]
    },
    "admin": {
        "name": "Admin", 
        "emoji": "🔧", 
        "level": 2,
        "permissions": ["view_users", "view_allocations", "view_uat", "email_settings"]
    },
    "user": {
        "name": "User", 
        "emoji": "👤", 
        "level": 1,
        "permissions": ["create_allocation", "view_own_allocation", "create_uat", "view_own_uat"]
    }
}

# ==================== UAT CONFIGURATION ====================
UAT_STATUS_OPTIONS = [
    "Not Started",
    "In Progress",
    "Completed",
    "On Hold",
    "Cancelled"
]

UAT_RESULT_OPTIONS = [
    "Pending",
    "Pass",
    "Fail",
    "Partial Pass"
]

UAT_CATEGORY_TYPES = [
    "Build",
    "Change Request"
]

UAT_PRIORITY_OPTIONS = [
    "Critical",
    "High",
    "Medium",
    "Low"
]

# ==================== ALLOCATION CONFIGURATION ====================
SYSTEMS = [
    "INFORM",
    "VEEVA",
    "eCOA",
    "ePID",
    "CGM",
    "Others"
]

THERAPEUTIC_AREAS = [
    "Diabetic",
    "Obesity",
    "CKAD (Chronic Kidney Allograft Dysfunction)",
    "CagriSema & OLD-D",
    "Phase 1 & NIS",
    "Rare Disease",
    "Others"
]

TRIAL_CATEGORIES = [
    "Build",
    "Change Request - 01",
    "Change Request - 02",
    "Change Request - 03"
]

ROLES_ALLOCATION = ["TE1", "TE2", "Support Role"]

ACTIVITY_TYPES = [
    "Test Execution",
    "Test Case Development",
    "Test Planning",
    "UAT Support",
    "Automation",
    "Documentation",
    "Others"
]

# ==================== AUDIT CONFIGURATION ====================
AUDIT_ACTIONS = [
    "LOGIN",
    "LOGOUT",
    "CREATE",
    "UPDATE",
    "DELETE",
    "VIEW",
    "EXPORT",
    "APPROVE",
    "REJECT"
]

AUDIT_MODULES = [
    "Authentication",
    "User Management",
    "Allocation",
    "UAT Status",
    "Audit Trail",
    "Email Settings"
]

# ==================== EMAIL CONFIGURATION ====================
DEFAULT_EMAIL_CONFIG = {
    "enabled": False,
    "smtp_server": "",
    "smtp_port": 587,
    "sender_email": "",
    "sender_password": "",
    "use_tls": True,
    "notify_on_create": True,
    "notify_on_update": False,
    "admin_email": "superuser@testportal.com"
}

# Flask-Mail Configuration (from environment variables)
class EmailConfig:
    """Email configuration from environment variables"""
    MAIL_SERVER = os.getenv('EMAIL_HOST', 'smtp.office365.com')
    MAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.getenv('EMAIL_USER')
    MAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('EMAIL_USER')
    MAIL_FROM_NAME = os.getenv('EMAIL_FROM_NAME', 'Test Engineer Portal')
    EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'False').lower() == 'true'
    
    # Email recipients from environment
    EMAIL_ADMIN = os.getenv('EMAIL_ADMIN', '')
    EMAIL_MANAGER = os.getenv('EMAIL_MANAGER', '')
    EMAIL_CDP = os.getenv('EMAIL_CDP', '')
    
    @staticmethod
    def is_configured():
        """Check if email is properly configured"""
        return all([
            EmailConfig.MAIL_USERNAME,
            EmailConfig.MAIL_PASSWORD,
            EmailConfig.EMAIL_ENABLED
        ])
    
    @staticmethod
    def get_config_dict():
        """Get email configuration as dictionary for Flask app"""
        return {
            'MAIL_SERVER': EmailConfig.MAIL_SERVER,
            'MAIL_PORT': EmailConfig.MAIL_PORT,
            'MAIL_USE_TLS': EmailConfig.MAIL_USE_TLS,
            'MAIL_USE_SSL': EmailConfig.MAIL_USE_SSL,
            'MAIL_USERNAME': EmailConfig.MAIL_USERNAME,
            'MAIL_PASSWORD': EmailConfig.MAIL_PASSWORD,
            'MAIL_DEFAULT_SENDER': EmailConfig.MAIL_DEFAULT_SENDER,
            'MAIL_FROM_NAME': EmailConfig.MAIL_FROM_NAME,
            'EMAIL_ENABLED': EmailConfig.EMAIL_ENABLED
        }
    
    @staticmethod
    def get_recipients(recipient_type='all'):
        """Get email recipients based on type"""
        recipients = []
        if recipient_type in ['all', 'admin'] and EmailConfig.EMAIL_ADMIN:
            recipients.extend([e.strip() for e in EmailConfig.EMAIL_ADMIN.split(',') if e.strip()])
        if recipient_type in ['all', 'manager'] and EmailConfig.EMAIL_MANAGER:
            recipients.extend([e.strip() for e in EmailConfig.EMAIL_MANAGER.split(',') if e.strip()])
        if recipient_type in ['all', 'cdp'] and EmailConfig.EMAIL_CDP:
            recipients.extend([e.strip() for e in EmailConfig.EMAIL_CDP.split(',') if e.strip()])
        return list(set(recipients))  # Remove duplicates

# Email notification settings for different modules
EMAIL_NOTIFICATION_SETTINGS = {
    "uat": {
        "on_create": True,
        "on_update": False,
        "on_submit": True,
        "on_status_change": True,
        "recipients_type": "admin"  # admin, manager, cdp, or all
    },
    "allocation": {
        "on_create": True,
        "on_update": False,
        "recipients_type": "manager"
    },
    "change_request": {
        "on_create": True,
        "on_update": True,
        "on_approve": True,
        "recipients_type": "cdp"
    },
    "quality": {
        "on_create": True,
        "on_submit": True,
        "recipients_type": "admin"
    }
}

# ==================== VALIDATION RULES ====================
VALIDATION = {
    "min_password_length": 6,
    "max_activity_length": 200,
    "max_email_body_length": 5000,
    "max_reason_length": 200,
    "allowed_file_extensions": [".xlsx", ".csv", ".pdf"],
    "max_file_size_mb": 10
}

# ==================== UI CONFIGURATION ====================
COLORS = {
    "primary": "#667eea",
    "secondary": "#764ba2",
    "success": "#4CAF50",
    "danger": "#F44336",
    "warning": "#FF9800",
    "info": "#2196F3"
}

STATUS_COLORS = {
    "Completed": "green",
    "In Progress": "blue",
    "Not Started": "gray",
    "On Hold": "orange",
    "Cancelled": "red",
    "Pass": "green",
    "Fail": "red",
    "Pending": "gray",
    "Partial Pass": "orange"
}

STATUS_EMOJIS = {
    "Completed": "✅",
    "In Progress": "🔄",
    "Not Started": "⏳",
    "On Hold": "⏸️",
    "Cancelled": "❌",
    "Pass": "✅",
    "Fail": "❌",
    "Pending": "⏳",
    "Partial Pass": "⚠️"
}

# ==================== PAGINATION ====================
ITEMS_PER_PAGE = 20
MAX_DISPLAY_ITEMS = 100

# ==================== DATE FORMATS ====================
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DISPLAY_DATE_FORMAT = "%d %b %Y"
DISPLAY_DATETIME_FORMAT = "%d %b %Y %I:%M %p"

# ==================== CHANGE REQUEST CONFIGURATION ====================
CR_CATEGORIES = [
    "Rule Change",
    "Form Change"
]

CR_VERSION_OPTIONS = [
    "Version",
    "Versionless"
]

CR_IMPACT_OPTIONS = [
    "Yes",
    "No",
    "N/A"
]

# ==================== BACKUP CONFIGURATION ====================
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

BACKUP_CONFIG = {
    "enabled": True,
    "frequency": "weekly",
    "day_of_week": 6,
    "time": "00:00",
    "retention_count": 4,
    "auto_cleanup": True,
    "include_files": [
        "users.json",
        "allocations.json",
        "uat_records.json",
        "audit_logs.json",
        "trail_documents.json",
        "change_requests.json",
        "quality_records.json",
        "pending_users.json",
        "password_reset_requests.json",
        "email_config.json"
    ]
}

# ==================== DATA PROTECTION ====================
DATA_PROTECTION = {
    "enabled": True,
    "protection_level": "write_through_app_only",
    "verify_integrity": True,
    "log_all_access": True,
    "checksum_validation": True,
    "superuser_only_unlock": True,
    "backup_before_critical": True,
    "lock_status_file": os.path.join(DATA_DIR, ".protection_status.json")
}

PROTECTION_STATUS_FILE = os.path.join(DATA_DIR, ".protection_status.json")

# Backup file naming
BACKUP_DATE_FORMAT = "%Y-%m-%d_%H-%M-%S"
BACKUP_INFO_FILE = "backup_info.json"