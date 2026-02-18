"""
Database utilities for JSON file operations
"""
import json
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Data directory
DATA_DIR = Path(__file__).resolve().parents[1] / 'data'
PENDING_USERS_FILE = DATA_DIR / 'pending_users.json'
PASSWORD_RESET_FILE = DATA_DIR / 'password_reset_requests.json'
EMAIL_CONFIG_FILE = DATA_DIR / 'email_config.json'

def _ensure_data_dir():
    """Ensure data directory exists"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# GENERIC DATA LOADING/SAVING FUNCTIONS
# ============================================================================
def load_data(data_type: str) -> List[Dict]:
    """
    Generic function to load JSON data files
    Args:
        data_type: Name of the data file without .json extension
                  (e.g., 'trail_documents', 'audit_logs', 'users')
    Returns:
        List of dictionaries from the JSON file
    """
    try:
        _ensure_data_dir()
        file_path = DATA_DIR / f'{data_type}.json'
        
        if file_path.exists():
            with file_path.open('r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading {data_type}: {e}")
        return []

def save_data(data_type: str, data: List[Dict]) -> bool:
    """
    Generic function to save JSON data files
    Args:
        data_type: Name of the data file without .json extension
        data: List of dictionaries to save
    Returns:
        True if successful, False otherwise
    """
    try:
        _ensure_data_dir()
        file_path = DATA_DIR / f'{data_type}.json'
        
        with file_path.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving {data_type}: {e}")
        return False

# ============================================================================
# TRAIL DOCUMENTS HELPER FUNCTIONS
# ============================================================================
def load_trail_documents() -> List[Dict]:
    """Load trail documents"""
    return load_data('trail_documents')

def add_trail_document(document: Dict) -> bool:
    """Add a new trail document"""
    try:
        documents = load_trail_documents()
        
        # Generate ID if not present
        if 'id' not in document:
            document['id'] = str(uuid.uuid4())
        
        # Add timestamp
        if 'created_at' not in document:
            document['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        documents.append(document)
        return save_data('trail_documents', documents)
    except Exception as e:
        print(f"Error adding trail document: {e}")
        return False

def update_trail_document(document_id: str, updates: Dict) -> bool:
    """Update a trail document"""
    try:
        documents = load_trail_documents()
        
        for doc in documents:
            if doc.get('id') == document_id:
                doc.update(updates)
                doc['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                return save_data('trail_documents', documents)
        
        return False
    except Exception as e:
        print(f"Error updating trail document: {e}")
        return False

def delete_trail_document(document_id: str) -> bool:
    """Delete a trail document"""
    try:
        documents = load_trail_documents()
        documents = [doc for doc in documents if doc.get('id') != document_id]
        return save_data('trail_documents', documents)
    except Exception as e:
        print(f"Error deleting trail document: {e}")
        return False

def get_trail_document(document_id: str) -> Optional[Dict]:
    """Get a specific trail document by ID - can return None if not found"""
    documents = load_trail_documents()
    return next((doc for doc in documents if doc.get('id') == document_id), None)

# ============================================================================
# AUDIT LOGS HELPER FUNCTIONS
# ============================================================================
def load_audit_logs() -> List[Dict]:
    """Load audit logs"""
    return load_data('audit_logs')

def save_audit_logs(logs: List[Dict]) -> bool:
    """Save audit logs"""
    return save_data('audit_logs', logs)

def add_audit_log(log_entry: Dict) -> bool:
    """Add a new audit log entry"""
    try:
        logs = load_audit_logs()
        
        # Generate ID if not present
        if 'id' not in log_entry:
            log_entry['id'] = str(uuid.uuid4())
        
        # Add timestamp
        if 'timestamp' not in log_entry:
            log_entry['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        logs.append(log_entry)
        return save_audit_logs(logs)
    except Exception as e:
        print(f"Error adding audit log: {e}")
        return False

# ============================================================================
# PENDING USERS FUNCTIONS
# ============================================================================
def load_pending_users() -> List[Dict]:
    """Load pending users from JSON file"""
    try:
        _ensure_data_dir()
        if PENDING_USERS_FILE.exists():
            with PENDING_USERS_FILE.open('r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading pending users: {e}")
        return []

def save_pending_users(pending_users: List[Dict]) -> bool:
    """Save pending users to JSON file"""
    try:
        _ensure_data_dir()
        with PENDING_USERS_FILE.open('w', encoding='utf-8') as f:
            json.dump(pending_users, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving pending users: {e}")
        return False

# ============================================================================
# PASSWORD RESET FUNCTIONS
# ============================================================================
def load_password_reset_requests() -> List[Dict]:
    """Load password reset requests from JSON file"""
    try:
        _ensure_data_dir()
        if PASSWORD_RESET_FILE.exists():
            with PASSWORD_RESET_FILE.open('r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading password reset requests: {e}")
        return []

def save_password_reset_requests(requests: List[Dict]) -> bool:
    """Save password reset requests to JSON file"""
    try:
        _ensure_data_dir()
        with PASSWORD_RESET_FILE.open('w', encoding='utf-8') as f:
            json.dump(requests, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving password reset requests: {e}")
        return False

# ============================================================================
# EMAIL CONFIG FUNCTIONS
# ============================================================================
def load_email_config() -> Dict[str, Any]:
    """Load email configuration"""
    try:
        _ensure_data_dir()
        if EMAIL_CONFIG_FILE.exists():
            with EMAIL_CONFIG_FILE.open('r', encoding='utf-8') as f:
                return json.load(f)
        return {"enabled": False}
    except Exception as e:
        print(f"Error loading email config: {e}")
        return {"enabled": False}

def save_email_config(config: Dict[str, Any]) -> bool:
    """Save email configuration"""
    try:
        _ensure_data_dir()
        with EMAIL_CONFIG_FILE.open('w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving email config: {e}")
        return False