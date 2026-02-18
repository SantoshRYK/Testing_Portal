"""
Admin Blueprint - Complete User Management and Settings
Superuser, Manager, and Admin access levels
Session-based authentication
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, abort
from functools import wraps
from datetime import datetime
from services.user_service import (
    get_all_users,
    get_pending_users,
    approve_pending_user,
    reject_pending_user,
    get_pending_audit_reviewers,
    approve_audit_reviewer,
    reject_audit_reviewer,
    get_audit_reviewers,
    revoke_audit_reviewer,
    create_user,
    update_user_role,
    delete_user,
    get_user_statistics,
    get_password_reset_requests,  # ← ADD THIS
    get_pending_password_resets,   # ← ADD THIS
    approve_password_reset,         # ← ADD THIS
    reject_password_reset          # ← ADD THIS
)

# ← ADD THESE MISSING FUNCTIONS TO services/user_service.py or import from correct location

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ============================================================================
# AUTHENTICATION DECORATORS
# ============================================================================

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def superuser_required(f):
    """Decorator to require superuser access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        user = session.get('user', {})
        if user.get('role') != 'superuser':
            flash('Superuser access required', 'danger')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin or superuser access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        user = session.get('user', {})
        if user.get('role') not in ['superuser', 'admin']:
            flash('Admin access required', 'danger')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    """Decorator to require manager or superuser access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        user = session.get('user', {})
        if user.get('role') not in ['superuser', 'manager']:
            flash('Manager access required', 'danger')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# SUPERUSER PANEL
# ============================================================================

@admin_bp.route('/superuser')
@login_required
@superuser_required
def superuser():
    """Superuser control panel"""
    user = session.get('user', {})
    
    # Get counts for menu badges
    pending_users = get_pending_users()
    pending_resets = get_pending_password_resets()
    pending_reviewers = get_pending_audit_reviewers()
    
    # Get action from query parameter
    action = request.args.get('action', 'pending_approvals')
    
    # Get statistics
    stats = get_user_statistics()
    all_users = get_all_users()
    audit_reviewers = get_audit_reviewers()
    
    # Get password reset history
    all_resets = get_password_reset_requests()
    processed_resets = [r for r in all_resets if r.get('status') != 'pending']
    
    return render_template('admin/superuser.html',
                         user=user,
                         action=action,
                         pending_users=pending_users,
                         pending_resets=pending_resets,
                         pending_reviewers=pending_reviewers,
                         audit_reviewers=audit_reviewers,
                         all_users=all_users,
                         processed_resets=processed_resets[-10:],  # Last 10
                         stats=stats,
                         pending_count={
                             'users': len(pending_users),
                             'resets': len(pending_resets),
                             'reviewers': len(pending_reviewers)
                         })

# ============================================================================
# PENDING USER APPROVALS
# ============================================================================

@admin_bp.route('/approve-user/<username>', methods=['POST'])
@login_required
@superuser_required
def approve_user(username):
    """Approve pending user"""
    approved_role = request.form.get('approved_role', 'user')
    approved_by = session.get('user', {}).get('username', 'admin')
    
    success, message = approve_pending_user(username, approved_role, approved_by)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('admin.superuser', action='pending_approvals'))

@admin_bp.route('/reject-user/<username>', methods=['POST'])
@login_required
@superuser_required
def reject_user(username):
    """Reject pending user"""
    success, message = reject_pending_user(username)
    
    if success:
        flash(message, 'warning')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('admin.superuser', action='pending_approvals'))

# ============================================================================
# PASSWORD RESET APPROVALS
# ============================================================================

@admin_bp.route('/approve-reset/<request_id>', methods=['POST'])
@login_required
@superuser_required
def approve_reset(request_id):
    """Approve password reset"""
    approved_by = session.get('user', {}).get('username', 'admin')
    
    success, message = approve_password_reset(request_id, approved_by)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('admin.superuser', action='password_resets'))

@admin_bp.route('/reject-reset/<request_id>', methods=['POST'])
@login_required
@superuser_required
def reject_reset(request_id):
    """Reject password reset"""
    rejected_by = session.get('user', {}).get('username', 'admin')
    
    success, message = reject_password_reset(request_id, rejected_by)
    
    if success:
        flash(message, 'warning')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('admin.superuser', action='password_resets'))

# ============================================================================
# AUDIT REVIEWER APPROVALS
# ============================================================================

@admin_bp.route('/approve-reviewer/<username>', methods=['POST'])
@login_required
@superuser_required
def approve_reviewer(username):
    """Approve audit reviewer access"""
    approved_by = session.get('user', {}).get('username', 'admin')
    
    success, message = approve_audit_reviewer(username, approved_by)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('admin.superuser', action='audit_reviewers'))

@admin_bp.route('/reject-reviewer/<username>', methods=['POST'])
@login_required
@superuser_required
def reject_reviewer(username):
    """Reject audit reviewer request"""
    success, message = reject_audit_reviewer(username)
    
    if success:
        flash(message, 'warning')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('admin.superuser', action='audit_reviewers'))

@admin_bp.route('/revoke-reviewer/<username>', methods=['POST'])
@login_required
@superuser_required
def revoke_reviewer(username):
    """Revoke audit reviewer access"""
    revoked_by = session.get('user', {}).get('username', 'admin')
    
    success, message = revoke_audit_reviewer(username, revoked_by)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('admin.superuser', action='audit_reviewers'))

# ============================================================================
# CREATE USER DIRECTLY
# ============================================================================

@admin_bp.route('/create-user', methods=['POST'])
@login_required
@superuser_required
def create_user_direct():
    """Create user directly (superuser only)"""
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    role = request.form.get('role', 'user')
    created_by = session.get('user', {}).get('username', 'admin')
    
    if not username or not email or not password:
        flash('All fields are required', 'danger')
        return redirect(url_for('admin.superuser', action='add_user'))
    
    success, message = create_user(username, email, password, role, created_by)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('admin.superuser', action='add_user'))

# ============================================================================
# MANAGE USERS
# ============================================================================

@admin_bp.route('/update-role/<username>', methods=['POST'])
@login_required
@superuser_required
def update_role(username):
    """Update user role"""
    new_role = request.form.get('new_role', 'user')
    updated_by = session.get('user', {}).get('username', 'admin')
    
    success, message = update_user_role(username, new_role, updated_by)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('admin.superuser', action='manage_users'))

@admin_bp.route('/delete-user/<username>', methods=['POST'])
@login_required
@superuser_required
def delete_user_route(username):
    """Delete user"""
    current_username = session.get('user', {}).get('username', '')
    
    if username == current_username:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('admin.superuser', action='delete_user'))
    
    success, message = delete_user(username)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('admin.superuser', action='delete_user'))

# ============================================================================
# MANAGER PANEL
# ============================================================================

@admin_bp.route('/manager')
@login_required
@manager_required
def manager():
    """Manager control panel"""
    user = session.get('user', {})
    
    # Get team statistics
    stats = get_user_statistics()
    all_users = get_all_users()
    team_members = {u: d for u, d in all_users.items() if d.get('role') == 'user'}
    
    return render_template('admin/manager.html',
                         user=user,
                         stats=stats,
                         team_members=team_members)

# ============================================================================
# ADMIN USER PANEL
# ============================================================================

@admin_bp.route('/admin-user')
@login_required
@admin_required
def admin_user():
    """Admin user management panel"""
    user = session.get('user', {})
    
    # Get all users
    all_users = get_all_users()
    stats = get_user_statistics()
    
    # Get filter
    role_filter = request.args.get('role', 'All')
    
    # Apply filter
    if role_filter != 'All':
        filtered_users = {u: d for u, d in all_users.items() if d.get('role') == role_filter}
    else:
        filtered_users = all_users
    
    return render_template('admin/admin_user.html',
                         user=user,
                         all_users=filtered_users,
                         stats=stats,
                         role_filter=role_filter)

# ============================================================================
# EMAIL SETTINGS
# ============================================================================

@admin_bp.route('/email-settings', methods=['GET', 'POST'])
@login_required
@admin_required
def email_settings():
    """Email configuration settings"""
    user = session.get('user', {})
    
    if request.method == 'POST':
        # TODO: Implement email settings save
        flash('Email settings updated successfully (Feature under construction)', 'info')
        return redirect(url_for('admin.email_settings'))
    
    email_config = {
        'smtp_server': '',
        'smtp_port': '587',
        'smtp_user': '',
        'from_email': '',
        'use_tls': True
    }
    
    return render_template('admin/email_settings.html',
                         email_config=email_config,
                         user=user)