# utils/auth_flask.py
"""
Flask Authentication and Authorization Utilities
"""
import hashlib
from functools import wraps
from flask import session, flash, redirect, url_for, abort
from typing import Optional

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hashed password"""
    return hash_password(password) == hashed_password

def get_current_user() -> str:
    """Get current logged-in user"""
    return session.get('username', '')

def get_current_role() -> str:
    """Get current user role"""
    return session.get('role', '')

def is_logged_in() -> bool:
    """Check if user is logged in"""
    return session.get('logged_in', False)

def is_superuser() -> bool:
    """Check if current user is superuser"""
    return get_current_role() == 'superuser'

def is_manager() -> bool:
    """Check if current user is manager"""
    return get_current_role() == 'manager'

def is_admin() -> bool:
    """Check if current user is admin"""
    return get_current_role() == 'admin'

def is_cdp() -> bool:
    """Check if current user is CDP"""
    return get_current_role() == 'cdp'

def is_regular_user() -> bool:
    """Check if current user is regular user"""
    return get_current_role() == 'user'

# ✅ NEW: Check if user is audit reviewer
def is_audit_reviewer() -> bool:
    """Check if current user has audit reviewer access"""
    return session.get('is_audit_reviewer', False) or is_superuser()

def can_manage_users() -> bool:
    """Check if user can manage other users"""
    return get_current_role() in ['superuser', 'admin']

def can_view_all_data() -> bool:
    """Check if user can view all data"""
    return get_current_role() in ['superuser', 'admin', 'manager']

def login_user(username: str, role: str, is_audit_reviewer: bool = False):
    """Log in user and set session"""
    session['logged_in'] = True
    session['username'] = username
    session['role'] = role
    session['is_audit_reviewer'] = is_audit_reviewer  # ✅ NEW
    session.permanent = True

def logout_user():
    """Log out user"""
    session.clear()

# Decorators
def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            flash('⚠️ Please login to access this page', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    """Decorator to require specific role(s)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not is_logged_in():
                flash('⚠️ Please login to access this page', 'warning')
                return redirect(url_for('auth.login'))
            
            user_role = get_current_role()
            if user_role not in roles:
                flash(f'❌ Access Denied: This page requires {" or ".join(roles)} role', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def superuser_required(f):
    """Decorator to require superuser access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            flash('⚠️ Please login to access this page', 'warning')
            return redirect(url_for('auth.login'))
        
        if not is_superuser():
            flash('❌ Access Denied: Superuser access required', 'danger')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

# ✅ NEW: Audit reviewer decorator
def audit_reviewer_required(f):
    """Decorator to require audit reviewer access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            flash('⚠️ Please login to access this page', 'warning')
            return redirect(url_for('auth.login'))
        
        if not is_audit_reviewer():
            flash('❌ Access Denied: Audit Reviewer access required', 'danger')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            flash('⚠️ Please login to access this page', 'warning')
            return redirect(url_for('auth.login'))
        
        if not can_manage_users():
            flash('❌ Access Denied: Admin access required', 'danger')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function