# services/user_service.py
"""
User management business logic
"""
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from utils.database import (
    load_users, save_users, get_user, user_exists,
    load_pending_users, save_pending_users,
    load_password_reset_requests, save_password_reset_requests
)
from utils.auth import hash_password, get_current_user
from utils.validators import validate_email, validate_password, validate_username
from services.audit_service import log_user_action

def create_user(username: str, email: str, password: str, role: str = "user", created_by: str = None) -> Tuple[bool, str]:
    """Create new user"""
    try:
        # Validate inputs
        valid, msg = validate_username(username)
        if not valid:
            return False, msg
        
        valid, msg = validate_email(email)
        if not valid:
            return False, msg
        
        valid, msg = validate_password(password)
        if not valid:
            return False, msg
        
        # Check if user exists
        if user_exists(username):
            return False, "Username already exists"
        
        # Create user
        users = load_users()
        users[username] = {
            "password": hash_password(password),
            "email": email,
            "role": role,
            "status": "active",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "created_by": created_by or get_current_user(),
            # ✅ NEW: Initialize audit reviewer fields
            "is_audit_reviewer": False,
            "audit_reviewer_requested": False,
            "audit_reviewer_justification": None,
            "audit_reviewer_approved_by": None,
            "audit_reviewer_approved_at": None
        }
        
        if save_users(users):
            # Log action
            log_user_action("CREATE", "User Management", f"Created user: {username} with role: {role}")
            return True, f"User '{username}' created successfully"
        else:
            return False, "Failed to save user"
    
    except Exception as e:
        return False, f"Error creating user: {str(e)}"

def update_user_role(username: str, new_role: str) -> Tuple[bool, str]:
    """Update user role"""
    try:
        users = load_users()
        
        if username not in users:
            return False, "User not found"
        
        old_role = users[username].get('role')
        users[username]['role'] = new_role
        users[username]['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        users[username]['updated_by'] = get_current_user()
        
        if save_users(users):
            log_user_action("UPDATE", "User Management", f"Updated {username} role from {old_role} to {new_role}")
            return True, f"User '{username}' role updated to {new_role}"
        else:
            return False, "Failed to update user"
    
    except Exception as e:
        return False, f"Error updating user: {str(e)}"

def delete_user(username: str) -> Tuple[bool, str]:
    """Delete user"""
    try:
        users = load_users()
        
        if username not in users:
            return False, "User not found"
        
        if username == "superuser":
            return False, "Cannot delete superuser"
        
        user_role = users[username].get('role')
        del users[username]
        
        if save_users(users):
            log_user_action("DELETE", "User Management", f"Deleted user: {username} (role: {user_role})")
            return True, f"User '{username}' deleted successfully"
        else:
            return False, "Failed to delete user"
    
    except Exception as e:
        return False, f"Error deleting user: {str(e)}"

def approve_pending_user(username: str, approved_role: str) -> Tuple[bool, str]:
    """Approve pending user registration"""
    try:
        pending_users = load_pending_users()
        
        # Find pending user
        pending_user = None
        for user in pending_users:
            if user.get('username') == username:
                pending_user = user
                break
        
        if not pending_user:
            return False, "Pending user not found"
        
        # Create active user
        users = load_users()
        users[username] = {
            "password": pending_user['password'],
            "email": pending_user['email'],
            "role": approved_role,
            "status": "active",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "approved_by": get_current_user(),
            # ✅ NEW: Include audit reviewer fields from pending user
            "is_audit_reviewer": False,
            "audit_reviewer_requested": pending_user.get('audit_reviewer_requested', False),
            "audit_reviewer_justification": pending_user.get('audit_reviewer_justification'),
            "audit_reviewer_approved_by": None,
            "audit_reviewer_approved_at": None
        }
        
        if save_users(users):
            # Remove from pending
            pending_users = [u for u in pending_users if u.get('username') != username]
            save_pending_users(pending_users)
            
            log_user_action("APPROVE", "User Management", f"Approved user: {username} as {approved_role}")
            return True, f"User '{username}' approved as {approved_role}"
        else:
            return False, "Failed to approve user"
    
    except Exception as e:
        return False, f"Error approving user: {str(e)}"

def reject_pending_user(username: str) -> Tuple[bool, str]:
    """Reject pending user registration"""
    try:
        pending_users = load_pending_users()
        pending_users = [u for u in pending_users if u.get('username') != username]
        
        if save_pending_users(pending_users):
            log_user_action("REJECT", "User Management", f"Rejected user registration: {username}")
            return True, f"Registration for '{username}' rejected"
        else:
            return False, "Failed to reject user"
    
    except Exception as e:
        return False, f"Error rejecting user: {str(e)}"

# ✅ NEW: Get pending audit reviewer requests
def get_pending_audit_reviewers() -> List[Dict]:
    """Get all users who requested audit reviewer access but not yet approved"""
    try:
        users = load_users()
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

# ✅ NEW: Approve audit reviewer access
def approve_audit_reviewer(username: str) -> Tuple[bool, str]:
    """Approve audit reviewer access for a user"""
    try:
        users = load_users()
        
        if username not in users:
            return False, "User not found"
        
        user = users[username]
        
        if not user.get('audit_reviewer_requested', False):
            return False, "User has not requested audit reviewer access"
        
        if user.get('is_audit_reviewer', False):
            return False, "User already has audit reviewer access"
        
        # Grant audit reviewer access
        users[username]['is_audit_reviewer'] = True
        users[username]['audit_reviewer_requested'] = False
        users[username]['audit_reviewer_approved_by'] = get_current_user()
        users[username]['audit_reviewer_approved_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if save_users(users):
            log_user_action(
                "APPROVE_AUDIT_REVIEWER", 
                "User Management", 
                f"Granted audit reviewer access to: {username}"
            )
            return True, f"Audit Reviewer access granted to '{username}'"
        else:
            return False, "Failed to save changes"
    
    except Exception as e:
        return False, f"Error approving audit reviewer: {str(e)}"

# ✅ NEW: Reject audit reviewer request
def reject_audit_reviewer(username: str) -> Tuple[bool, str]:
    """Reject audit reviewer access request"""
    try:
        users = load_users()
        
        if username not in users:
            return False, "User not found"
        
        user = users[username]
        
        if not user.get('audit_reviewer_requested', False):
            return False, "User has not requested audit reviewer access"
        
        # Reject request
        users[username]['audit_reviewer_requested'] = False
        users[username]['audit_reviewer_justification'] = None
        
        if save_users(users):
            log_user_action(
                "REJECT_AUDIT_REVIEWER", 
                "User Management", 
                f"Rejected audit reviewer request from: {username}"
            )
            return True, f"Audit Reviewer request rejected for '{username}'"
        else:
            return False, "Failed to save changes"
    
    except Exception as e:
        return False, f"Error rejecting audit reviewer: {str(e)}"

# ✅ NEW: Request audit reviewer access
def request_audit_reviewer_access(username: str, justification: str) -> Tuple[bool, str]:
    """Request audit reviewer access for an existing user"""
    try:
        users = load_users()
        
        if username not in users:
            return False, "User not found"
        
        user = users[username]
        
        if user.get('is_audit_reviewer', False):
            return False, "User already has audit reviewer access"
        
        if user.get('audit_reviewer_requested', False):
            return False, "Audit reviewer access already requested, pending approval"
        
        # Request access
        users[username]['audit_reviewer_requested'] = True
        users[username]['audit_reviewer_justification'] = justification
        
        if save_users(users):
            log_user_action(
                "REQUEST_AUDIT_REVIEWER", 
                "User Management", 
                f"Requested audit reviewer access: {username}"
            )
            return True, "Audit Reviewer access request submitted for approval"
        else:
            return False, "Failed to save request"
    
    except Exception as e:
        return False, f"Error requesting audit reviewer access: {str(e)}"

# ✅ NEW: Revoke audit reviewer access
def revoke_audit_reviewer(username: str) -> Tuple[bool, str]:
    """Revoke audit reviewer access from a user"""
    try:
        users = load_users()
        
        if username not in users:
            return False, "User not found"
        
        user = users[username]
        
        if not user.get('is_audit_reviewer', False):
            return False, "User does not have audit reviewer access"
        
        # Revoke access
        users[username]['is_audit_reviewer'] = False
        users[username]['audit_reviewer_approved_by'] = None
        users[username]['audit_reviewer_approved_at'] = None
        
        if save_users(users):
            log_user_action(
                "REVOKE_AUDIT_REVIEWER", 
                "User Management", 
                f"Revoked audit reviewer access from: {username}"
            )
            return True, f"Audit Reviewer access revoked from '{username}'"
        else:
            return False, "Failed to save changes"
    
    except Exception as e:
        return False, f"Error revoking audit reviewer: {str(e)}"

# ✅ MODIFIED: Updated to include audit reviewer stats
def get_user_statistics() -> Dict:
    """Get user statistics"""
    users = load_users()
    
    stats = {
        'total': len(users),
        'by_role': {},
        'by_status': {},
        'pending': len(load_pending_users()),
        'audit_reviewers': 0,  # ✅ NEW
        'pending_audit_reviewers': 0  # ✅ NEW
    }
    
    for user in users.values():
        role = user.get('role', 'unknown')
        status = user.get('status', 'active')
        
        stats['by_role'][role] = stats['by_role'].get(role, 0) + 1
        stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
        
        # ✅ NEW: Count audit reviewers
        if user.get('is_audit_reviewer', False):
            stats['audit_reviewers'] += 1
        
        # ✅ NEW: Count pending audit reviewer requests
        if (user.get('audit_reviewer_requested', False) and 
            not user.get('is_audit_reviewer', False)):
            stats['pending_audit_reviewers'] += 1
    
    return stats

# ✅ NEW: Get all audit reviewers
def get_audit_reviewers() -> List[Dict]:
    """Get all users with audit reviewer access"""
    try:
        users = load_users()
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