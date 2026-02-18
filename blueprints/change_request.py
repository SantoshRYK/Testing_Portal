"""
Change Request Blueprint - Change request tracker
Session-based authentication
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps

change_request_bp = Blueprint('change_request', __name__, url_prefix='/change-request')

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
# MAIN ROUTES
# ============================================================================
@change_request_bp.route('/')
@change_request_bp.route('/main')
@login_required
def main():
    """Change Request main page"""
    user = session.get('user', {})
    role = user.get('role', 'user')
    username = user.get('username', '')
    
    # TODO: Get actual change request statistics
    stats = {
        'total': 0,
        'open': 0,
        'in_progress': 0,
        'completed': 0,
        'recent': []
    }
    
    return render_template('change_request/main.html', 
                         user=user,
                         stats=stats)

@change_request_bp.route('/list')
@login_required
def list_view():
    """List all change requests"""
    user = session.get('user', {})
    role = user.get('role', 'user')
    username = user.get('username', '')
    
    # Get filter parameters
    status_filter = request.args.get('status', 'All')
    priority_filter = request.args.get('priority', 'All')
    type_filter = request.args.get('type', 'All')
    
    # TODO: Get actual change requests from service
    # Placeholder - empty list for now
    change_requests = []
    
    # Filter based on role - users see only their requests
    if role == 'user':
        change_requests = [cr for cr in change_requests if cr.get('created_by') == username]
    
    # Apply filters
    if status_filter != 'All':
        change_requests = [cr for cr in change_requests if cr.get('status') == status_filter]
    
    if priority_filter != 'All':
        change_requests = [cr for cr in change_requests if cr.get('priority') == priority_filter]
    
    if type_filter != 'All':
        change_requests = [cr for cr in change_requests if cr.get('type') == type_filter]
    
    # Filter options for dropdowns
    statuses = ['Open', 'In Progress', 'Completed', 'Cancelled']
    priorities = ['Low', 'Medium', 'High', 'Critical']
    types = ['Enhancement', 'Bug Fix', 'Configuration', 'Documentation']
    
    return render_template('change_request/list.html',
                         change_requests=change_requests,
                         statuses=statuses,
                         priorities=priorities,
                         types=types,
                         filters={
                             'status': status_filter,
                             'priority': priority_filter,
                             'type': type_filter
                         },
                         user=user)

@change_request_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new change request"""
    user = session.get('user', {})
    username = user.get('username', '')
    
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        priority = request.form.get('priority', 'Medium')
        cr_type = request.form.get('type', 'Enhancement')
        trial_id = request.form.get('trial_id', '').strip()
        
        # Validation
        if not title or not description:
            flash('Title and Description are required', 'danger')
            return render_template('change_request/create.html', user=user)
        
        # TODO: Save to database using service
        # Placeholder
        flash('✅ Change request created successfully! (Feature under construction)', 'success')
        return redirect(url_for('change_request.list_view'))
    
    return render_template('change_request/create.html', user=user)

@change_request_bp.route('/view/<cr_id>')
@login_required
def view(cr_id):
    """View single change request"""
    user = session.get('user', {})
    role = user.get('role', 'user')
    username = user.get('username', '')
    
    # TODO: Get actual change request from service
    # Placeholder
    change_request = {
        '_id': cr_id,
        'title': 'Sample Change Request',
        'description': 'This is a placeholder change request',
        'status': 'Open',
        'priority': 'Medium',
        'type': 'Enhancement',
        'trial_id': 'DEMO-001',
        'created_by': username,
        'created_at': '2024-01-15',
        'updated_at': '2024-01-15'
    }
    
    # Check permissions
    if role not in ['superuser', 'admin', 'manager']:
        if change_request.get('created_by') != username:
            flash('You do not have permission to view this change request', 'danger')
            return redirect(url_for('change_request.list_view'))
    
    return render_template('change_request/view.html',
                         change_request=change_request,
                         user=user)

@change_request_bp.route('/edit/<cr_id>', methods=['GET', 'POST'])
@login_required
def edit(cr_id):
    """Edit change request"""
    user = session.get('user', {})
    role = user.get('role', 'user')
    username = user.get('username', '')
    
    # TODO: Get actual change request from service
    # Placeholder
    change_request = {
        '_id': cr_id,
        'title': 'Sample Change Request',
        'description': 'This is a placeholder change request',
        'status': 'Open',
        'priority': 'Medium',
        'type': 'Enhancement',
        'trial_id': 'DEMO-001',
        'created_by': username
    }
    
    # Check permissions
    if role not in ['superuser', 'admin', 'manager']:
        if change_request.get('created_by') != username:
            flash('You do not have permission to edit this change request', 'danger')
            return redirect(url_for('change_request.list_view'))
    
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        status = request.form.get('status', 'Open')
        priority = request.form.get('priority', 'Medium')
        cr_type = request.form.get('type', 'Enhancement')
        
        # Validation
        if not title or not description:
            flash('Title and Description are required', 'danger')
            return render_template('change_request/edit.html',
                                 change_request=change_request,
                                 user=user)
        
        # TODO: Update in database using service
        # Placeholder
        flash('✅ Change request updated successfully! (Feature under construction)', 'success')
        return redirect(url_for('change_request.view', cr_id=cr_id))
    
    return render_template('change_request/edit.html',
                         change_request=change_request,
                         user=user)

@change_request_bp.route('/delete/<cr_id>', methods=['POST'])
@login_required
def delete(cr_id):
    """Delete change request"""
    user = session.get('user', {})
    role = user.get('role', 'user')
    username = user.get('username', '')
    
    # TODO: Get actual change request from service
    # Placeholder
    change_request = {
        '_id': cr_id,
        'created_by': username
    }
    
    # Check permissions - Only creator or admin can delete
    if role not in ['superuser', 'admin']:
        if change_request.get('created_by') != username:
            flash('You do not have permission to delete this change request', 'danger')
            return redirect(url_for('change_request.list_view'))
    
    # TODO: Delete from database using service
    # Placeholder
    flash('✅ Change request deleted successfully! (Feature under construction)', 'success')
    return redirect(url_for('change_request.list_view'))

@change_request_bp.route('/dashboard')
@login_required
def dashboard():
    """Change Request dashboard with statistics and charts"""
    user = session.get('user', {})
    role = user.get('role', 'user')
    
    # Check if user is manager/admin
    if role not in ['superuser', 'admin', 'manager']:
        flash('Dashboard access is restricted to managers and admins', 'warning')
        return redirect(url_for('change_request.main'))
    
    # TODO: Get actual statistics from service
    stats = {
        'total': 0,
        'open': 0,
        'in_progress': 0,
        'completed': 0,
        'cancelled': 0,
        'by_priority': {
            'Critical': 0,
            'High': 0,
            'Medium': 0,
            'Low': 0
        },
        'by_type': {
            'Enhancement': 0,
            'Bug Fix': 0,
            'Configuration': 0,
            'Documentation': 0
        }
    }
    
    return render_template('change_request/dashboard.html',
                         stats=stats,
                         user=user)

# ============================================================================
# API ENDPOINTS
# ============================================================================
@change_request_bp.route('/api/list')
@login_required
def api_list():
    """API endpoint to get change requests as JSON"""
    user = session.get('user', {})
    role = user.get('role', 'user')
    username = user.get('username', '')
    
    # TODO: Get actual change requests from service
    change_requests = []
    
    # Filter based on role
    if role == 'user':
        change_requests = [cr for cr in change_requests if cr.get('created_by') == username]
    
    return jsonify(change_requests)

@change_request_bp.route('/api/stats')
@login_required
def api_stats():
    """API endpoint to get change request statistics"""
    # TODO: Calculate from actual records
    stats = {
        'total': 0,
        'open': 0,
        'in_progress': 0,
        'completed': 0,
        'cancelled': 0
    }
    
    return jsonify(stats)