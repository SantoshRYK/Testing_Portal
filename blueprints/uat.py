"""
UAT Blueprint - User Acceptance Testing records
✅ WITH EMAIL NOTIFICATIONS
✅ WITH DATE DIFFERENCE VALIDATION
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app
from functools import wraps
from datetime import datetime
from config import EmailConfig, EMAIL_NOTIFICATION_SETTINGS, UAT_STATUS_OPTIONS, UAT_RESULT_OPTIONS
from services.uat_service import (
    create_uat_record, get_uat_records_by_role, get_uat_record_by_id,
    update_uat_record, delete_uat_record, get_uat_statistics, get_trial_ids
)

uat_bp = Blueprint('uat', __name__, url_prefix='/uat')

# ============================================================================
# AUTHENTICATION DECORATOR
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

# ============================================================================
# EMAIL HELPER FUNCTIONS
# ============================================================================
def send_uat_notification(record, action='created'):
    """Send email notification for UAT record"""
    if not EmailConfig.is_configured():
        print("⚠️  Email not configured - skipping notification")
        return
    
    settings = EMAIL_NOTIFICATION_SETTINGS.get('uat', {})
    action_key = f'on_{action}'
    
    if not settings.get(action_key, False):
        print(f"ℹ️  Email notifications disabled for action: {action}")
        return
    
    try:
        from utils.email_handler import send_email, create_uat_email_body
        
        recipients = EmailConfig.get_recipients('admin')
        
        if not recipients:
            print("⚠️  No recipients configured for UAT notifications")
            return
        
        portal_url = request.url_root if request else ""
        body_html = create_uat_email_body(record, action, portal_url)
        subject = f"UAT Record {action.capitalize()} - {record.get('trial_id', 'N/A')}"
        
        result = send_email(recipients, subject, body_html)
        
        if result['success']:
            print(f"✅ Email notification sent for UAT {action}")
        else:
            print(f"❌ Failed to send email: {result['message']}")
            
    except Exception as e:
        print(f"❌ Error sending email notification: {str(e)}")

# ============================================================================
# MAIN ROUTES
# ============================================================================
@uat_bp.route('/')
@uat_bp.route('/main')
@login_required
def main():
    """UAT main page"""
    user = session.get('user', {})
    role = user.get('role', 'user')
    
    # Manager sees different tabs
    show_create = role != 'manager'
    
    return render_template('uat/main.html', 
                         user=user, 
                         show_create=show_create)

@uat_bp.route('/dashboard')
@login_required
def dashboard():
    """UAT dashboard with statistics"""
    user = session.get('user', {})
    role = user.get('role', 'user')
    username = user.get('username', '')
    
    records = get_uat_records_by_role(role, username)
    stats = get_uat_statistics(records)
    
    return render_template('uat/dashboard.html', 
                         user=user,
                         stats=stats,
                         records=records)

@uat_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create UAT record"""
    user = session.get('user', {})
    username = user.get('username', '')
    role = user.get('role', 'user')
    
    # Manager cannot create
    if role == 'manager':
        flash('Managers cannot create UAT records', 'warning')
        return redirect(url_for('uat.main'))
    
    if request.method == 'POST':
        # Get form data
        trial_id = request.form.get('trial_id', '').strip()
        uat_round = request.form.get('uat_round', '').strip()
        category_type = request.form.get('category_type', 'Build')
        category_detail = request.form.get('category_detail', '').strip()
        
        # Construct category
        if category_type == 'Build':
            category = 'Build'
        else:
            if not category_detail:
                flash('Change Request details are required', 'danger')
                return render_template('uat/create.html', 
                                     user=user,
                                     email_configured=EmailConfig.is_configured(),
                                     status_options=UAT_STATUS_OPTIONS,
                                     result_options=UAT_RESULT_OPTIONS,
                                     form_data=request.form)
            category = f'Change Request - {category_detail}'
        
        planned_start_date = request.form.get('planned_start_date', '')
        planned_end_date = request.form.get('planned_end_date', '')
        actual_start_date = request.form.get('actual_start_date', '')
        actual_end_date = request.form.get('actual_end_date', '')
        date_difference_reason = request.form.get('date_difference_reason', '').strip()
        status = request.form.get('status', 'Not Started')
        result = request.form.get('result', 'Pending')
        email_body = request.form.get('email_body', '').strip()
        send_notification = request.form.get('send_notification', 'off') == 'on'
        
        # Validation
        if not all([trial_id, uat_round, planned_start_date, planned_end_date]):
            flash('Please fill in all required fields', 'danger')
            return render_template('uat/create.html', 
                                 user=user,
                                 email_configured=EmailConfig.is_configured(),
                                 status_options=UAT_STATUS_OPTIONS,
                                 result_options=UAT_RESULT_OPTIONS,
                                 form_data=request.form)
        
        # Create record data
        uat_data = {
            'trial_id': trial_id,
            'uat_round': uat_round,
            'category': category,
            'category_type': category_type,
            'planned_start_date': planned_start_date,
            'planned_end_date': planned_end_date,
            'actual_start_date': actual_start_date if actual_start_date else None,
            'actual_end_date': actual_end_date if actual_end_date else None,
            'date_difference_reason': date_difference_reason,
            'status': status,
            'result': result,
            'email_body': email_body
        }
        
        # Create record
        success, message = create_uat_record(uat_data, username)
        
        if success:
            flash(f'✅ {message}', 'success')
            
            # Send email if requested
            if send_notification:
                uat_data['id'] = 'NEW'  # Placeholder for email
                uat_data['created_by'] = username
                uat_data['tester_name'] = user.get('name', username)
                send_uat_notification(uat_data, 'created')
                flash('📧 Email notification sent', 'info')
            
            return redirect(url_for('uat.view_list'))
        else:
            flash(f'❌ {message}', 'danger')
            return render_template('uat/create.html', 
                                 user=user,
                                 email_configured=EmailConfig.is_configured(),
                                 status_options=UAT_STATUS_OPTIONS,
                                 result_options=UAT_RESULT_OPTIONS,
                                 form_data=request.form)
    
    # GET request
    email_configured = EmailConfig.is_configured()
    
    return render_template('uat/create.html', 
                         user=user, 
                         email_configured=email_configured,
                         status_options=UAT_STATUS_OPTIONS,
                         result_options=UAT_RESULT_OPTIONS)

@uat_bp.route('/records')
@uat_bp.route('/list')
@login_required
def view_list():
    """View all UAT records"""
    user = session.get('user', {})
    role = user.get('role', 'user')
    username = user.get('username', '')
    
    records = get_uat_records_by_role(role, username)
    stats = get_uat_statistics(records)
    trial_ids = get_trial_ids()
    
    # Get filter parameters
    filter_trial = request.args.get('trial_id', 'All')
    filter_status = request.args.get('status', 'All')
    filter_result = request.args.get('result', 'All')
    filter_category = request.args.get('category', 'All')
    
    # Apply filters
    if filter_trial != 'All':
        records = [r for r in records if r.get('trial_id') == filter_trial]
    if filter_status != 'All':
        records = [r for r in records if r.get('status') == filter_status]
    if filter_result != 'All':
        records = [r for r in records if r.get('result') == filter_result]
    if filter_category != 'All':
        records = [r for r in records if r.get('category_type') == filter_category]
    
    return render_template('uat/list.html', 
                         records=records,
                         stats=stats,
                         trial_ids=trial_ids,
                         user=user,
                         filters={
                             'trial_id': filter_trial,
                             'status': filter_status,
                             'result': filter_result,
                             'category': filter_category
                         },
                         status_options=UAT_STATUS_OPTIONS,
                         result_options=UAT_RESULT_OPTIONS)

@uat_bp.route('/view/<record_id>')
@login_required
def view(record_id):
    """View single UAT record"""
    user = session.get('user', {})
    role = user.get('role', 'user')
    username = user.get('username', '')
    
    record = get_uat_record_by_id(record_id)
    
    if not record:
        flash('UAT record not found', 'danger')
        return redirect(url_for('uat.view_list'))
    
    # Check permissions
    if role not in ['superuser', 'admin', 'manager']:
        if record.get('created_by') != username:
            flash('You do not have permission to view this record', 'danger')
            return redirect(url_for('uat.view_list'))
    
    email_configured = EmailConfig.is_configured()
    
    return render_template('uat/view.html', 
                         record=record,
                         user=user,
                         email_configured=email_configured)

@uat_bp.route('/edit/<record_id>', methods=['GET', 'POST'])
@login_required
def edit(record_id):
    """Edit UAT record"""
    user = session.get('user', {})
    role = user.get('role', 'user')
    username = user.get('username', '')
    
    record = get_uat_record_by_id(record_id)
    
    if not record:
        flash('UAT record not found', 'danger')
        return redirect(url_for('uat.view_list'))
    
    # Check permissions
    if role not in ['superuser', 'admin']:
        if record.get('created_by') != username:
            flash('You do not have permission to edit this record', 'danger')
            return redirect(url_for('uat.view_list'))
    
    if request.method == 'POST':
        # Similar to create logic...
        # Get form data and update
        trial_id = request.form.get('trial_id', '').strip()
        uat_round = request.form.get('uat_round', '').strip()
        category_type = request.form.get('category_type', 'Build')
        category_detail = request.form.get('category_detail', '').strip()
        
        if category_type == 'Build':
            category = 'Build'
        else:
            category = f'Change Request - {category_detail}' if category_detail else ''
        
        uat_data = {
            'trial_id': trial_id,
            'uat_round': uat_round,
            'category': category,
            'category_type': category_type,
            'planned_start_date': request.form.get('planned_start_date'),
            'planned_end_date': request.form.get('planned_end_date'),
            'actual_start_date': request.form.get('actual_start_date') or None,
            'actual_end_date': request.form.get('actual_end_date') or None,
            'date_difference_reason': request.form.get('date_difference_reason', '').strip(),
            'status': request.form.get('status'),
            'result': request.form.get('result'),
            'email_body': request.form.get('email_body', '').strip()
        }
        
        success, message = update_uat_record(record_id, uat_data, username)
        
        if success:
            flash(f'✅ {message}', 'success')
            
            # Send email if requested
            if request.form.get('send_notification') == 'on':
                record.update(uat_data)
                send_uat_notification(record, 'updated')
                flash('📧 Email notification sent', 'info')
            
            return redirect(url_for('uat.view', record_id=record_id))
        else:
            flash(f'❌ {message}', 'danger')
    
    email_configured = EmailConfig.is_configured()
    
    return render_template('uat/edit.html', 
                         record=record,
                         user=user,
                         email_configured=email_configured,
                         status_options=UAT_STATUS_OPTIONS,
                         result_options=UAT_RESULT_OPTIONS)

@uat_bp.route('/delete/<record_id>', methods=['POST'])
@login_required
def delete(record_id):
    """Delete UAT record"""
    user = session.get('user', {})
    role = user.get('role', 'user')
    username = user.get('username', '')
    
    record = get_uat_record_by_id(record_id)
    
    if not record:
        flash('UAT record not found', 'danger')
        return redirect(url_for('uat.view_list'))
    
    # Check permissions
    if role not in ['superuser', 'admin']:
        if record.get('created_by') != username:
            flash('You do not have permission to delete this record', 'danger')
            return redirect(url_for('uat.view_list'))
    
    success, message = delete_uat_record(record_id)
    
    if success:
        flash(f'✅ {message}', 'success')
    else:
        flash(f'❌ {message}', 'danger')
    
    return redirect(url_for('uat.view_list'))

@uat_bp.route('/send_email/<record_id>', methods=['POST'])
@login_required
def send_email_notification(record_id):
    """Send email notification for a specific record"""
    record = get_uat_record_by_id(record_id)
    
    if not record:
        flash('UAT record not found', 'danger')
        return redirect(url_for('uat.view_list'))
    
    send_uat_notification(record, 'submitted')
    flash('📧 Email notification sent successfully!', 'success')
    
    return redirect(url_for('uat.view', record_id=record_id))