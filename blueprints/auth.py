"""
Authentication Blueprint - Flask Compatible
Handles login, logout, registration, and password management
✅ WITH AUDIT REVIEWER SUPPORT
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
from datetime import datetime
from typing import Optional
import re

# Import services
from services.user_service import (
    authenticate_user,
    get_user_by_username,
    get_user_by_email,
    get_all_users,
    change_password,
    reset_password,
    delete_user
)

# Import new functions for registration and password reset
from utils.auth import hash_password
from utils.database import (
    load_pending_users,
    save_pending_users,
    load_password_reset_requests,
    save_password_reset_requests,
    load_email_config
)
from utils.validators import validate_email, validate_password, validate_username
from utils.email_handler import send_email

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            user = session.get('user')
            if user and user.get('role') not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('home.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_client_ip() -> str:
    """Get client IP address"""
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.remote_addr or '0.0.0.0'


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login with audit reviewer support"""
    if 'user' in session:
        return redirect(url_for('home.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('auth/login.html')
        
        # Authenticate user
        user = authenticate_user(username, password)
        
        if user:
            # ✅ CRITICAL FIX: Load full user data to get is_audit_reviewer flag
            full_user = get_user_by_username(username)
            
            if full_user:
                # Add audit reviewer flag to session user
                user['is_audit_reviewer'] = full_user.get('is_audit_reviewer', False)
            else:
                user['is_audit_reviewer'] = False
            
            # Store user in session
            session['user'] = user
            session['login_time'] = datetime.now().isoformat()
            session.permanent = bool(remember)
            
            # ✅ Welcome message with audit reviewer badge
            welcome_msg = f'Welcome back, {user["username"]}!'
            
            if user.get('is_audit_reviewer'):
                welcome_msg += ' 🔍 (Audit Reviewer)'
                flash('✅ Audit Reviewer access enabled - You can view all trail documents', 'info')
            
            flash(welcome_msg, 'success')
            
            # Redirect to next page or home
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('home.index'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    user_data = session.get('user', {})
    username = user_data.get('username', 'Unknown') if user_data else 'Unknown'
    session.clear()
    flash(f'Goodbye, {username}! You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration - creates pending user"""
    if 'user' in session:
        return redirect(url_for('home.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        requested_role = request.form.get('requested_role', 'user')
        request_audit_reviewer = request.form.get('request_audit_reviewer') == 'on'
        audit_justification = request.form.get('audit_justification', '').strip()
        
        # Validate inputs
        valid, error_msg = validate_username(username)
        if not valid:
            flash(error_msg, 'danger')
            return render_template('auth/login.html')
        
        valid, error_msg = validate_email(email)
        if not valid:
            flash(error_msg, 'danger')
            return render_template('auth/login.html')
        
        valid, error_msg = validate_password(password, confirm_password)
        if not valid:
            flash(error_msg, 'danger')
            return render_template('auth/login.html')
        
        # Check if audit reviewer justification is provided
        if request_audit_reviewer and not audit_justification:
            flash('Please provide justification for Audit Reviewer access', 'danger')
            return render_template('auth/login.html')
        
        # Check if user already exists
        if get_user_by_username(username):
            flash('Username already exists. Please choose a different username.', 'danger')
            return render_template('auth/login.html')
        
        if get_user_by_email(email):
            flash('Email already registered. Please use a different email.', 'danger')
            return render_template('auth/login.html')
        
        # Check pending users
        pending_users = load_pending_users()
        username_exists = any(p['username'] == username for p in pending_users)
        
        if username_exists:
            flash('Username already exists or pending approval!', 'danger')
            return render_template('auth/login.html')
        
        # Create pending user
        pending_user = {
            "username": username,
            "password": hash_password(password),
            "email": email,
            "requested_role": requested_role,
            "status": "pending",
            "requested_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "audit_reviewer_requested": request_audit_reviewer,
            "audit_reviewer_justification": audit_justification if request_audit_reviewer else None
        }
        
        pending_users.append(pending_user)
        
        if save_pending_users(pending_users):
            flash('✅ Registration submitted! Your account is pending Super User approval.', 'success')
            
            if requested_role == "cdp":
                flash('You have requested CDP role - you will only have access to Change Request Tracker.', 'info')
            
            if request_audit_reviewer:
                flash('🔍 Your Audit Reviewer access request has also been submitted for approval.', 'info')
            
            # Send email notification to admin
            try:
                config = load_email_config()
                if config.get("enabled", False):
                    admin_email = config.get("admin_email", "")
                    if admin_email:
                        role_emoji = "📊" if requested_role == "cdp" else "👤"
                        
                        email_body = f"""
                        <h3>New User Registration</h3>
                        <p>A new user has registered:</p>
                        <ul>
                            <li><strong>Username:</strong> {username}</li>
                            <li><strong>Email:</strong> {email}</li>
                            <li><strong>Requested Role:</strong> {role_emoji} {requested_role.upper()}</li>
                            <li><strong>Requested At:</strong> {pending_user['requested_at']}</li>
                        """
                        
                        if requested_role == "cdp":
                            email_body += """
                            <li><strong>⚠️ Special Access:</strong> CDP - Change Request Tracker Only</li>
                        """
                        
                        if request_audit_reviewer:
                            email_body += f"""
                            <li><strong>⚠️ Audit Reviewer Access:</strong> REQUESTED 🔍</li>
                            <li><strong>Justification:</strong> {audit_justification}</li>
                        """
                        
                        email_body += """
                        </ul>
                        <p>Please log in to approve or reject this registration.</p>
                        """
                        
                        send_email(admin_email, "New User Registration - Test Engineer Portal", email_body)
            except Exception as e:
                print(f"Failed to send email: {e}")
            
            return redirect(url_for('auth.login'))
        else:
            flash('Failed to submit registration. Please try again.', 'danger')
    
    return render_template('auth/login.html')


# ============================================================================
# PASSWORD MANAGEMENT ROUTES
# ============================================================================

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password_route():
    """Change password for logged-in user"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate new password
        valid, error_msg = validate_password(new_password, confirm_password)
        if not valid:
            flash(error_msg, 'danger')
            return render_template('auth/change_password.html')
        
        user_data = session.get('user', {})
        username = user_data.get('username', '')
        
        if not username:
            flash('Session expired. Please log in again.', 'danger')
            return redirect(url_for('auth.login'))
        
        success, message = change_password(username, current_password, new_password)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('home.index'))
        else:
            flash(message, 'danger')
    
    return render_template('auth/change_password.html')


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        reason = request.form.get('reason', '').strip()
        
        # Validate password
        valid, error_msg = validate_password(new_password, confirm_password)
        if not valid:
            flash(error_msg, 'danger')
            return render_template('auth/login.html')
        
        # Check if user exists
        user = get_user_by_username(username)
        if not user:
            flash('Username not found!', 'danger')
            return render_template('auth/login.html')
        
        if user.get('email', '').lower() != email.lower():
            flash("Email doesn't match our records!", 'danger')
            return render_template('auth/login.html')
        
        # Check for existing pending requests
        reset_requests = load_password_reset_requests()
        existing_request = any(
            r['username'] == username and r['status'] == 'pending'
            for r in reset_requests
        )
        
        if existing_request:
            flash('You already have a pending password reset request!', 'warning')
            return render_template('auth/login.html')
        
        # Create reset request
        reset_request = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "username": username,
            "email": email,
            "new_password": hash_password(new_password),
            "reason": reason if reason else "User requested password reset",
            "status": "pending",
            "requested_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        reset_requests.append(reset_request)
        
        if save_password_reset_requests(reset_requests):
            flash('Password reset request submitted!', 'success')
            flash('Your request has been sent to the Super User for approval.', 'info')
            flash('Once approved, you can login with your new password.', 'info')
            
            # Send email notification
            try:
                config = load_email_config()
                if config.get("enabled", False):
                    admin_email = config.get("admin_email", "")
                    if admin_email:
                        email_body = f"""
                        <h3>🔑 New Password Reset Request</h3>
                        <p>A user has requested a password reset:</p>
                        <table style="width: 100%; border-collapse: collapse;">
                          <tr style="background-color: #f8f9fa;">
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Username:</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{username}</td>
                          </tr>
                          <tr>
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Email:</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{email}</td>
                          </tr>
                          <tr style="background-color: #f8f9fa;">
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Reason:</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{reset_request['reason']}</td>
                          </tr>
                          <tr>
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Requested At:</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{reset_request['requested_at']}</td>
                          </tr>
                        </table>
                        <p><strong>⚠️ Action Required:</strong> Please log in to approve or reject this request.</p>
                        """
                        send_email(admin_email, "Password Reset Request - Test Engineer Portal", email_body)
            except Exception as e:
                print(f"Failed to send email: {e}")
            
            return redirect(url_for('auth.login'))
        else:
            flash('Failed to submit request. Please try again.', 'danger')
    
    return render_template('auth/login.html')


# ============================================================================
# API ENDPOINTS (for AJAX calls)
# ============================================================================

@auth_bp.route('/api/check-username/<username>')
def check_username(username):
    """Check if username is available (API endpoint)"""
    user = get_user_by_username(username)
    pending_users = load_pending_users()
    pending_exists = any(p['username'] == username for p in pending_users)
    
    return jsonify({'available': user is None and not pending_exists})


@auth_bp.route('/api/check-email/<email>')
def check_email(email):
    """Check if email is available (API endpoint)"""
    user = get_user_by_email(email)
    pending_users = load_pending_users()
    pending_exists = any(p['email'].lower() == email.lower() for p in pending_users)
    
    return jsonify({'available': user is None and not pending_exists})