"""
User Service - Flask Compatible
Handles all user-related business logic using JSON file storage
Compatible with Streamlit's user data structure (username as key)
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Tuple, List
from utils.auth import hash_password

# Data file paths
DATA_DIR = Path(__file__).resolve().parents[1] / 'data'
USERS_FILE = DATA_DIR / 'users.json'
PENDING_USERS_FILE = DATA_DIR / 'pending_users.json'
PASSWORD_RESET_FILE = DATA_DIR / 'password_reset_requests.json'

def _ensure_data_file():
    """Ensure data directory and users file exist"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    if not USERS_FILE.exists():
        default_users = {
            "admin": {
                "password": hash_password("admin123"),
                "email": "admin@novotest.com",
                "role": "superuser",
                "is_audit_reviewer": True,
                "is_active": True,
                "status": "active",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        with USERS_FILE.open('w', encoding='utf-8') as f:
            json.dump(default_users, f, indent=4, ensure_ascii=False)
    
    if not PENDING_USERS_FILE.exists():
        with PENDING_USERS_FILE.open('w', encoding='utf-8') as f:
            json.dump([], f, indent=4, ensure_ascii=False)
    
    if not PASSWORD_RESET_FILE.exists():
        with PASSWORD_RESET_FILE.open('w', encoding='utf-8') as f:
            json.dump([], f, indent=4, ensure_ascii=False)

def _load_users() -> Dict[str, Dict]:
    """Load all users from file"""
    try:
        _ensure_data_file()
        with USERS_FILE.open('r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                print("Warning: users.json is empty, initializing...")
                _ensure_data_file()
                with USERS_FILE.open('r', encoding='utf-8') as f:
                    return json.load(f)
            
            data = json.loads(content)
            
            if not isinstance(data, dict):
                print(f"Error: users.json contains {type(data)}, expected dict")
                return {}
            
            return data
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in users.json: {e}")
        return {}
    except Exception as e:
        print(f"Error loading users: {e}")
        return {}

def _save_users(users: Dict[str, Dict]) -> bool:
    """Save users to file"""
    try:
        if not isinstance(users, dict):
            print(f"Error: Attempted to save non-dict as users: {type(users)}")
            return False
        
        with USERS_FILE.open('w', encoding='utf-8') as f:
            json.dump(users, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving users: {e}")
        return False

def _load_pending_users() -> List[Dict]:
    """Load pending users"""
    try:
        _ensure_data_file()
        with PENDING_USERS_FILE.open('r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading pending users: {e}")
        return []

def _save_pending_users(pending: List[Dict]) -> bool:
    """Save pending users"""
    try:
        with PENDING_USERS_FILE.open('w', encoding='utf-8') as f:
            json.dump(pending, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving pending users: {e}")
        return False

def _load_password_resets() -> List[Dict]:
    """Load password reset requests"""
    try:
        _ensure_data_file()
        with PASSWORD_RESET_FILE.open('r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading password resets: {e}")
        return []

def _save_password_resets(resets: List[Dict]) -> bool:
    """Save password reset requests"""
    try:
        with PASSWORD_RESET_FILE.open('w', encoding='utf-8') as f:
            json.dump(resets, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving password resets: {e}")
        return False

# ============================================================================
# USER CRUD OPERATIONS
# ============================================================================

def get_user_by_username(username: str) -> Optional[Dict]:
    """Get user data by username"""
    users = _load_users()
    
    if not isinstance(users, dict):
        return None
    
    user = users.get(username)
    
    if user and isinstance(user, dict):
        return user
    
    return None

def get_user_by_email(email: str) -> Optional[Dict]:
    """Get user data by email"""
    users = _load_users()
    
    if not isinstance(users, dict):
        return None
    
    for username, user_data in users.items():
        if isinstance(user_data, dict) and user_data.get('email', '').lower() == email.lower():
            return user_data
    
    return None

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate user with username and password"""
    users = _load_users()
    
    if username not in users:
        return None
    
    user = users[username]
    
    if not isinstance(user, dict):
        return None
    
    hashed_input = hash_password(password)
    stored_hash = user.get('password', '')
    
    if stored_hash != hashed_input:
        return None
    
    is_active = user.get('is_active', True)
    if not is_active:
        return None
    
    status = user.get('status', 'active')
    if status != 'active':
        return None
    
    # ✅ CRITICAL FIX: Include is_audit_reviewer in returned user data
    user_copy = user.copy()
    user_copy.pop('password', None)
    user_copy['username'] = username
    user_copy['is_audit_reviewer'] = user.get('is_audit_reviewer', False)  # ✅ ADD THIS LINE
    
    return user_copy

def get_all_users() -> Dict[str, Dict]:
    """Get all users (without passwords)"""
    users = _load_users()
    
    if not isinstance(users, dict):
        return {}
    
    result = {}
    for username, user_data in users.items():
        if isinstance(user_data, dict):
            user_copy = user_data.copy()
            user_copy.pop('password', None)
            user_copy['username'] = username
            result[username] = user_copy
    
    return result

def create_user(username: str, email: str, password: str, role: str = "user", created_by: Optional[str] = None) -> Tuple[bool, str]:
    """Create new user"""
    try:
        users = _load_users()
        
        if username in users:
            return False, "Username already exists"
        
        new_user = {
            'password': hash_password(password),
            'email': email,
            'role': role,
            'status': 'active',
            'is_active': True,
            'is_audit_reviewer': False,
            'audit_reviewer_requested': False,
            'audit_reviewer_justification': None,
            'audit_reviewer_approved_by': None,
            'audit_reviewer_approved_at': None,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'created_by': created_by if created_by else 'system'
        }
        
        users[username] = new_user
        
        if _save_users(users):
            return True, f"User '{username}' created successfully"
        return False, "Failed to save user"
    except Exception as e:
        return False, f"Error: {str(e)}"

def update_user_role(username: str, new_role: str, updated_by: Optional[str] = None) -> Tuple[bool, str]:
    """Update user role"""
    try:
        users = _load_users()
        
        if username not in users:
            return False, "User not found"
        
        old_role = users[username].get('role')
        users[username]['role'] = new_role
        users[username]['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        users[username]['updated_by'] = updated_by if updated_by else 'system'
        
        if _save_users(users):
            return True, f"User '{username}' role updated from {old_role} to {new_role}"
        return False, "Failed to update user"
    except Exception as e:
        return False, f"Error: {str(e)}"

def delete_user(username: str) -> Tuple[bool, str]:
    """Delete user"""
    try:
        users = _load_users()
        
        if username not in users:
            return False, "User not found"
        
        if username == "superuser" or username == "admin":
            return False, "Cannot delete system admin accounts"
        
        # Check if last superuser
        superusers = [u for u, data in users.items() if data.get('role') == 'superuser']
        if len(superusers) == 1 and username in superusers:
            return False, "Cannot delete the last superuser"
        
        user_role = users[username].get('role')
        del users[username]
        
        if _save_users(users):
            return True, f"User '{username}' (role: {user_role}) deleted successfully"
        return False, "Failed to delete user"
    except Exception as e:
        return False, f"Error: {str(e)}"

# ============================================================================
# PENDING USER MANAGEMENT
# ============================================================================

def get_pending_users() -> List[Dict]:
    """Get all pending user registrations"""
    return _load_pending_users()

def approve_pending_user(username: str, approved_role: str, approved_by: Optional[str] = None) -> Tuple[bool, str]:
    """Approve pending user registration"""
    try:
        pending_users = _load_pending_users()
        
        pending_user = None
        for user in pending_users:
            if user.get('username') == username:
                pending_user = user
                break
        
        if not pending_user:
            return False, "Pending user not found"
        
        users = _load_users()
        users[username] = {
            "password": pending_user['password'],
            "email": pending_user['email'],
            "role": approved_role,
            "status": "active",
            "is_active": True,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "approved_by": approved_by if approved_by else 'admin',
            "is_audit_reviewer": False,
            "audit_reviewer_requested": pending_user.get('audit_reviewer_requested', False),
            "audit_reviewer_justification": pending_user.get('audit_reviewer_justification'),
            "audit_reviewer_approved_by": None,
            "audit_reviewer_approved_at": None
        }
        
        if _save_users(users):
            pending_users = [u for u in pending_users if u.get('username') != username]
            _save_pending_users(pending_users)
            return True, f"User '{username}' approved as {approved_role}"
        
        return False, "Failed to approve user"
    except Exception as e:
        return False, f"Error: {str(e)}"

def reject_pending_user(username: str) -> Tuple[bool, str]:
    """Reject pending user registration"""
    try:
        pending_users = _load_pending_users()
        pending_users = [u for u in pending_users if u.get('username') != username]
        
        if _save_pending_users(pending_users):
            return True, f"Registration for '{username}' rejected"
        return False, "Failed to reject user"
    except Exception as e:
        return False, f"Error: {str(e)}"

# ============================================================================
# PASSWORD RESET MANAGEMENT
# ============================================================================

def get_password_reset_requests() -> List[Dict]:
    """Get all password reset requests"""
    return _load_password_resets()

def get_pending_password_resets() -> List[Dict]:
    """Get pending password reset requests"""
    resets = _load_password_resets()
    return [r for r in resets if r.get('status') == 'pending']

def approve_password_reset(request_id: str, approved_by: Optional[str] = None) -> Tuple[bool, str]:
    """Approve password reset request"""
    try:
        reset_requests = _load_password_resets()
        
        request_found = None
        for req in reset_requests:
            if req.get('id') == request_id:
                request_found = req
                break
        
        if not request_found:
            return False, "Reset request not found"
        
        username = request_found.get('username')
        new_password = request_found.get('new_password')
        
        # Update user password
        users = _load_users()
        if username not in users:
            return False, "User not found"
        
        users[username]['password'] = new_password
        users[username]['password_reset_by'] = approved_by if approved_by else 'admin'
        users[username]['password_reset_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if _save_users(users):
            # Update request status
            for req in reset_requests:
                if req.get('id') == request_id:
                    req['status'] = 'approved'
                    req['approved_by'] = approved_by if approved_by else 'admin'
                    req['approved_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    break
            
            _save_password_resets(reset_requests)
            return True, f"Password reset approved for '{username}'"
        
        return False, "Failed to update password"
    except Exception as e:
        return False, f"Error: {str(e)}"

def reject_password_reset(request_id: str, rejected_by: Optional[str] = None) -> Tuple[bool, str]:
    """Reject password reset request"""
    try:
        reset_requests = _load_password_resets()
        
        request_found = None
        for req in reset_requests:
            if req.get('id') == request_id:
                request_found = req
                break
        
        if not request_found:
            return False, "Reset request not found"
        
        username = request_found.get('username')
        
        # Update request status
        for req in reset_requests:
            if req.get('id') == request_id:
                req['status'] = 'rejected'
                req['rejected_by'] = rejected_by if rejected_by else 'admin'
                req['rejected_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                break
        
        if _save_password_resets(reset_requests):
            return True, f"Password reset rejected for '{username}'"
        
        return False, "Failed to update request"
    except Exception as e:
        return False, f"Error: {str(e)}"

# ============================================================================
# AUDIT REVIEWER MANAGEMENT
# ============================================================================

def get_pending_audit_reviewers() -> List[Dict]:
    """Get all users who requested audit reviewer access but not yet approved"""
    try:
        users = _load_users()
        pending_reviewers = []
        
        for username, user_data in users.items():
            if (user_data.get('status') == 'active' and 
                user_data.get('audit_reviewer_requested', False) and 
                not user_data.get('is_audit_reviewer', False)):
                
                pending_reviewers.append({
                    'username': username,
                    'email': user_data.get('email'),
                    'role': user_data.get('role'),
                    'audit_reviewer_justification': user_data.get('audit_reviewer_justification'),
                    'created_at': user_data.get('created_at'),
                    'approved_by': user_data.get('approved_by')
                })
        
        return pending_reviewers
    except Exception as e:
        print(f"Error getting pending reviewers: {str(e)}")
        return []

def approve_audit_reviewer(username: str, approved_by: Optional[str] = None) -> Tuple[bool, str]:
    """Approve audit reviewer access for a user"""
    try:
        users = _load_users()
        
        if username not in users:
            return False, "User not found"
        
        user = users[username]
        
        if not user.get('audit_reviewer_requested', False):
            return False, "User has not requested audit reviewer access"
        
        if user.get('is_audit_reviewer', False):
            return False, "User already has audit reviewer access"
        
        users[username]['is_audit_reviewer'] = True
        users[username]['audit_reviewer_requested'] = False
        users[username]['audit_reviewer_approved_by'] = approved_by if approved_by else 'admin'
        users[username]['audit_reviewer_approved_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if _save_users(users):
            return True, f"Audit Reviewer access granted to '{username}'"
        return False, "Failed to save changes"
    except Exception as e:
        return False, f"Error: {str(e)}"

def reject_audit_reviewer(username: str) -> Tuple[bool, str]:
    """Reject audit reviewer access request"""
    try:
        users = _load_users()
        
        if username not in users:
            return False, "User not found"
        
        user = users[username]
        
        if not user.get('audit_reviewer_requested', False):
            return False, "User has not requested audit reviewer access"
        
        users[username]['audit_reviewer_requested'] = False
        users[username]['audit_reviewer_justification'] = None
        
        if _save_users(users):
            return True, f"Audit Reviewer request rejected for '{username}'"
        return False, "Failed to save changes"
    except Exception as e:
        return False, f"Error: {str(e)}"

def revoke_audit_reviewer(username: str, revoked_by: Optional[str] = None) -> Tuple[bool, str]:
    """Revoke audit reviewer access from a user"""
    try:
        users = _load_users()
        
        if username not in users:
            return False, "User not found"
        
        user = users[username]
        
        if not user.get('is_audit_reviewer', False):
            return False, "User does not have audit reviewer access"
        
        users[username]['is_audit_reviewer'] = False
        users[username]['audit_reviewer_approved_by'] = None
        users[username]['audit_reviewer_approved_at'] = None
        users[username]['audit_reviewer_revoked_by'] = revoked_by if revoked_by else 'admin'
        users[username]['audit_reviewer_revoked_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if _save_users(users):
            return True, f"Audit Reviewer access revoked from '{username}'"
        return False, "Failed to save changes"
    except Exception as e:
        return False, f"Error: {str(e)}"

def get_audit_reviewers() -> List[Dict]:
    """Get all users with audit reviewer access"""
    try:
        users = _load_users()
        reviewers = []
        
        for username, user_data in users.items():
            if user_data.get('is_audit_reviewer', False):
                reviewers.append({
                    'username': username,
                    'email': user_data.get('email'),
                    'role': user_data.get('role'),
                    'approved_by': user_data.get('audit_reviewer_approved_by'),
                    'approved_at': user_data.get('audit_reviewer_approved_at')
                })
        
        return reviewers
    except Exception as e:
        print(f"Error getting audit reviewers: {str(e)}")
        return []

def request_audit_reviewer_access(username: str, justification: str) -> Tuple[bool, str]:
    """Request audit reviewer access for an existing user"""
    try:
        users = _load_users()
        
        if username not in users:
            return False, "User not found"
        
        user = users[username]
        
        if user.get('is_audit_reviewer', False):
            return False, "User already has audit reviewer access"
        
        if user.get('audit_reviewer_requested', False):
            return False, "Audit reviewer access already requested, pending approval"
        
        users[username]['audit_reviewer_requested'] = True
        users[username]['audit_reviewer_justification'] = justification
        
        if _save_users(users):
            return True, "Audit Reviewer access request submitted for approval"
        return False, "Failed to save request"
    except Exception as e:
        return False, f"Error: {str(e)}"

# ============================================================================
# STATISTICS
# ============================================================================

def get_user_statistics() -> Dict:
    """Get user statistics"""
    users = _load_users()
    pending = _load_pending_users()
    
    stats = {
        'total': len(users),
        'by_role': {},
        'by_status': {},
        'pending': len(pending),
        'audit_reviewers': 0,
        'pending_audit_reviewers': 0
    }
    
    for user in users.values():
        role = user.get('role', 'unknown')
        status = user.get('status', 'active')
        
        stats['by_role'][role] = stats['by_role'].get(role, 0) + 1
        stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
        
        if user.get('is_audit_reviewer', False):
            stats['audit_reviewers'] += 1
        
        if (user.get('audit_reviewer_requested', False) and 
            not user.get('is_audit_reviewer', False)):
            stats['pending_audit_reviewers'] += 1
    
    return stats

def change_password(username: str, old_password: str, new_password: str) -> Tuple[bool, str]:
    """Change user password"""
    try:
        users = _load_users()
        
        if username not in users:
            return False, "User not found"
        
        user = users[username]
        
        if hash_password(old_password) != user.get('password', ''):
            return False, "Current password is incorrect"
        
        users[username]['password'] = hash_password(new_password)
        users[username]['password_changed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if _save_users(users):
            return True, "Password changed successfully"
        return False, "Failed to save password"
    except Exception as e:
        return False, f"Error: {str(e)}"

def reset_password(username: str, new_password: str) -> Tuple[bool, str]:
    """Reset user password (admin function)"""
    try:
        users = _load_users()
        
        if username not in users:
            return False, "User not found"
        
        users[username]['password'] = hash_password(new_password)
        users[username]['password_reset_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if _save_users(users):
            return True, "Password reset successfully"
        return False, "Failed to save password"
    except Exception as e:
        return False, f"Error: {str(e)}"