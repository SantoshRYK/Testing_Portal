"""
Allocations Blueprint - Complete with Manager Dashboard
Session-based authentication with Advanced Filtering
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session, send_file
from functools import wraps
from datetime import datetime
import io
import json
from services.allocation_service import (
    create_allocation_record,
    get_all_allocations,
    get_allocation_by_id,
    update_allocation_record,
    delete_allocation_record,
    get_allocations_by_role,
    get_allocation_statistics,
    search_allocations,
    calculate_engineer_efficiency
)
from config import SYSTEMS, THERAPEUTIC_AREAS, ROLES_ALLOCATION

allocations_bp = Blueprint('allocations', __name__, url_prefix='/allocations')

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def safe_session_set(key: str, value, default: str = '') -> None:
    """Safely set session value with type checking"""
    session[key] = str(value) if value is not None else default

def get_unique_sorted(items):
    """Get unique non-None sorted values"""
    return sorted([item for item in set(items) if item is not None])

def get_allocations_by_user(username):
    """Get allocations created by specific user"""
    all_allocations = get_all_allocations()
    return [a for a in all_allocations if a.get('created_by') == username]

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

def role_required(*roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            user = session.get('user', {})
            if user.get('role') not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('home.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============================================================================
# MAIN ROUTES
# ============================================================================
@allocations_bp.route('/')
@allocations_bp.route('/index')
@login_required
def index():
    """Allocations landing page with overview and quick actions"""
    user = session.get('user', {})
    role = user.get('role', '')
    username = user.get('username', '')
    
    # Get allocations based on role
    if role == 'user':
        all_allocations = get_allocations_by_user(username)
    else:
        all_allocations = get_all_allocations()
    
    # Calculate statistics
    stats = {
        'total': len(all_allocations),
        'build': len([a for a in all_allocations if a.get('trial_category_type') == 'Build']),
        'change_request': len([a for a in all_allocations if a.get('trial_category_type') == 'Change Request']),
        'systems': len(set(a.get('system') for a in all_allocations if a.get('system')))
    }
    
    # Get recent allocations (last 5)
    recent_allocations = sorted(
        all_allocations, 
        key=lambda x: x.get('created_at', ''), 
        reverse=True
    )[:5]
    
    return render_template('allocations/index.html',
                         stats=stats,
                         recent_allocations=recent_allocations,
                         user=user)

@allocations_bp.route('/list')
@login_required
def list_view():
    """List allocations - User sees own, Manager sees all"""
    user = session.get('user', {})
    role = user.get('role', '')
    username = user.get('username', '')
    
    # Get allocations based on role
    allocations = get_allocations_by_role(role, username)
    
    # Calculate stats for metrics
    stats = {
        'total': len(allocations),
        'build': sum(1 for a in allocations if a.get('trial_category_type') == 'Build'),
        'change_request': sum(1 for a in allocations if 'Change Request' in a.get('trial_category', '')),
        'systems': len(set(a.get('system') for a in allocations if a.get('system')))
    }
    
    return render_template('allocations/list.html', 
                         allocations=allocations,
                         stats=stats,
                         user=user)

@allocations_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new allocation"""
    user = session.get('user', {})
    
    if request.method == 'POST':
        # Get form data
        data = request.form.to_dict()
        
        # Validation
        required_fields = ['test_engineer_name', 'trial_id', 'system', 'role', 'activity', 'start_date', 'end_date']
        for field in required_fields:
            if not data.get(field):
                flash(f'{field.replace("_", " ").title()} is required', 'danger')
                return render_template('allocations/create.html',
                                     systems=SYSTEMS,
                                     therapeutic_areas=THERAPEUTIC_AREAS,
                                     roles=ROLES_ALLOCATION,
                                     form_data=data,
                                     user=user)
        
        # Date validation
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
            if end_date < start_date:
                flash('End date must be after start date', 'danger')
                return render_template('allocations/create.html',
                                     systems=SYSTEMS,
                                     therapeutic_areas=THERAPEUTIC_AREAS,
                                     roles=ROLES_ALLOCATION,
                                     form_data=data,
                                     user=user)
        except ValueError:
            flash('Invalid date format', 'danger')
            return render_template('allocations/create.html',
                                 systems=SYSTEMS,
                                 therapeutic_areas=THERAPEUTIC_AREAS,
                                 roles=ROLES_ALLOCATION,
                                 form_data=data,
                                 user=user)
        
        # Handle trial category
        category_type = data.get('category_type', 'Build')
        if category_type == 'Change Request':
            category_detail = data.get('category_detail', '').strip()
            if not category_detail:
                flash('Please enter Change Request details', 'danger')
                return render_template('allocations/create.html',
                                     systems=SYSTEMS,
                                     therapeutic_areas=THERAPEUTIC_AREAS,
                                     roles=ROLES_ALLOCATION,
                                     form_data=data,
                                     user=user)
            data['trial_category'] = f"Change Request - {category_detail}"
            data['trial_category_type'] = 'Change Request'
        else:
            data['trial_category'] = 'Build'
            data['trial_category_type'] = 'Build'
        
        # Handle therapeutic area
        area_type = data.get('therapeutic_area_type', '')
        if area_type == 'Others':
            area_detail = data.get('therapeutic_area_other', '').strip()
            if not area_detail:
                flash('Please specify therapeutic area for Others', 'danger')
                return render_template('allocations/create.html',
                                     systems=SYSTEMS,
                                     therapeutic_areas=THERAPEUTIC_AREAS,
                                     roles=ROLES_ALLOCATION,
                                     form_data=data,
                                     user=user)
            data['therapeutic_area'] = f"Others - {area_detail}"
            data['therapeutic_area_type'] = 'Others'
        else:
            data['therapeutic_area'] = area_type or ''
            data['therapeutic_area_type'] = area_type or ''
        
        # Create allocation
        username = user.get('username', 'Unknown')
        success, message = create_allocation_record(data, username)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('allocations.list_view'))
        else:
            flash(message, 'danger')
    
    return render_template('allocations/create.html',
                         systems=SYSTEMS,
                         therapeutic_areas=THERAPEUTIC_AREAS,
                         roles=ROLES_ALLOCATION,
                         user=user)

@allocations_bp.route('/view/<allocation_id>')
@login_required
def view(allocation_id):
    """View single allocation"""
    user = session.get('user', {})
    allocation = get_allocation_by_id(allocation_id)
    
    if not allocation:
        flash('Allocation not found', 'danger')
        return redirect(url_for('allocations.list_view'))
    
    # Check permissions - User can only view their own
    if user.get('role') not in ['superuser', 'admin', 'manager']:
        if allocation.get('created_by') != user.get('username'):
            flash('You do not have permission to view this allocation', 'danger')
            return redirect(url_for('allocations.list_view'))
    
    return render_template('allocations/view.html', 
                         allocation=allocation,
                         user=user)

@allocations_bp.route('/edit/<allocation_id>', methods=['GET', 'POST'])
@login_required
def edit(allocation_id):
    """Edit allocation - Only creator or admin/superuser"""
    user = session.get('user', {})
    allocation = get_allocation_by_id(allocation_id)
    
    if not allocation:
        flash('Allocation not found', 'danger')
        return redirect(url_for('allocations.list_view'))
    
    # Check permissions - Manager CANNOT edit!
    role = user.get('role', '')
    creator = allocation.get('created_by', '')
    current_username = user.get('username', '')
    
    if role == 'manager':
        flash('Managers cannot edit allocations', 'warning')
        return redirect(url_for('allocations.list_view'))
    
    if role not in ['superuser', 'admin']:
        if creator != current_username:
            flash('You can only edit your own allocations', 'danger')
            return redirect(url_for('allocations.list_view'))
    
    if request.method == 'POST':
        data = request.form.to_dict()
        
        # Handle trial category
        category_type = data.get('category_type', 'Build')
        if category_type == 'Change Request':
            category_detail = data.get('category_detail', '').strip()
            if not category_detail:
                flash('Please enter Change Request details', 'danger')
                return render_template('allocations/edit.html',
                                     allocation=allocation,
                                     systems=SYSTEMS,
                                     therapeutic_areas=THERAPEUTIC_AREAS,
                                     roles=ROLES_ALLOCATION,
                                     user=user)
            data['trial_category'] = f"Change Request - {category_detail}"
            data['trial_category_type'] = 'Change Request'
        else:
            data['trial_category'] = 'Build'
            data['trial_category_type'] = 'Build'
        
        # Handle therapeutic area
        area_type = data.get('therapeutic_area_type', '')
        if area_type == 'Others':
            area_detail = data.get('therapeutic_area_other', '').strip()
            if not area_detail:
                flash('Please specify therapeutic area for Others', 'danger')
                return render_template('allocations/edit.html',
                                     allocation=allocation,
                                     systems=SYSTEMS,
                                     therapeutic_areas=THERAPEUTIC_AREAS,
                                     roles=ROLES_ALLOCATION,
                                     user=user)
            data['therapeutic_area'] = f"Others - {area_detail}"
            data['therapeutic_area_type'] = 'Others'
        else:
            data['therapeutic_area'] = area_type or ''
            data['therapeutic_area_type'] = area_type or ''
        
        username = user.get('username', 'Unknown')
        success, message = update_allocation_record(allocation_id, data, username)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('allocations.view', allocation_id=allocation_id))
        else:
            flash(message, 'danger')
    
    return render_template('allocations/edit.html',
                         allocation=allocation,
                         systems=SYSTEMS,
                         therapeutic_areas=THERAPEUTIC_AREAS,
                         roles=ROLES_ALLOCATION,
                         user=user)

@allocations_bp.route('/delete/<allocation_id>', methods=['POST'])
@login_required
def delete(allocation_id):
    """Delete allocation - Only creator or admin/superuser"""
    user = session.get('user', {})
    allocation = get_allocation_by_id(allocation_id)
    
    if not allocation:
        flash('Allocation not found', 'danger')
        return redirect(url_for('allocations.list_view'))
    
    # Check permissions - Manager CANNOT delete!
    role = user.get('role', '')
    creator = allocation.get('created_by', '')
    current_username = user.get('username', '')
    
    if role == 'manager':
        flash('Managers cannot delete allocations', 'warning')
        return redirect(url_for('allocations.list_view'))
    
    if role not in ['superuser', 'admin']:
        if creator != current_username:
            flash('You can only delete your own allocations', 'danger')
            return redirect(url_for('allocations.list_view'))
    
    success, message = delete_allocation_record(allocation_id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('allocations.list_view'))

@allocations_bp.route('/dashboard')
@login_required
@role_required('superuser', 'admin', 'manager')
def dashboard():
    """Manager dashboard with analytics and charts - with filtering"""
    user = session.get('user', {})
    
    # Get filter parameters from request
    filter_system = request.args.get('system', '')
    filter_category = request.args.get('trial_category', '')
    filter_therapeutic_area = request.args.get('therapeutic_area', '')
    filter_test_engineer = request.args.get('test_engineer', '')
    filter_role = request.args.get('role', '')
    filter_trial_id = request.args.get('trial_id', '')
    filter_created_by = request.args.get('created_by', '')
    filter_start_date = request.args.get('start_date', '')
    filter_end_date = request.args.get('end_date', '')
    
    # Get all allocations
    all_allocations = get_all_allocations()
    
    # Apply filters
    filtered_allocations = all_allocations
    
    if filter_system:
        filtered_allocations = [a for a in filtered_allocations if a.get('system') == filter_system]
    
    if filter_category:
        filtered_allocations = [a for a in filtered_allocations 
                               if a.get('trial_category_type') == filter_category or 
                               filter_category in a.get('trial_category', '')]
    
    if filter_therapeutic_area:
        filtered_allocations = [a for a in filtered_allocations 
                               if a.get('therapeutic_area_type') == filter_therapeutic_area or
                               filter_therapeutic_area in a.get('therapeutic_area', '')]
    
    if filter_test_engineer:
        filtered_allocations = [a for a in filtered_allocations 
                               if a.get('test_engineer_name') == filter_test_engineer]
    
    if filter_role:
        filtered_allocations = [a for a in filtered_allocations if a.get('role') == filter_role]
    
    if filter_trial_id:
        filtered_allocations = [a for a in filtered_allocations 
                               if filter_trial_id.lower() in a.get('trial_id', '').lower()]
    
    if filter_created_by:
        filtered_allocations = [a for a in filtered_allocations 
                               if a.get('created_by') == filter_created_by]
    
    # Date range filter
    if filter_start_date:
        try:
            start_date = datetime.strptime(filter_start_date, '%Y-%m-%d').date()
            filtered_allocations = [a for a in filtered_allocations 
                                   if datetime.strptime(a.get('start_date', '2024-01-01'), '%Y-%m-%d').date() >= start_date]
        except:
            pass
    
    if filter_end_date:
        try:
            end_date = datetime.strptime(filter_end_date, '%Y-%m-%d').date()
            filtered_allocations = [a for a in filtered_allocations 
                                   if datetime.strptime(a.get('end_date', '2024-12-31'), '%Y-%m-%d').date() <= end_date]
        except:
            pass
    
    # Calculate statistics from filtered data
    stats = {
        'total': len(filtered_allocations),
        'build': sum(1 for a in filtered_allocations if a.get('trial_category_type') == 'Build'),
        'change_request': sum(1 for a in filtered_allocations if a.get('trial_category_type') == 'Change Request'),
        'systems': len(set(a.get('system') for a in filtered_allocations if a.get('system')))
    }
    
    # Calculate engineer efficiency from filtered data
    efficiency_data = calculate_engineer_efficiency(filtered_allocations)
    
    # Get unique values for dropdowns (with None filtering)
    systems = get_unique_sorted(a.get('system') for a in all_allocations if a.get('system'))
    categories = get_unique_sorted(a.get('trial_category_type', 'Build') for a in all_allocations)
    therapeutic_areas = get_unique_sorted(a.get('therapeutic_area_type') for a in all_allocations if a.get('therapeutic_area_type'))
    test_engineers = get_unique_sorted(a.get('test_engineer_name') for a in all_allocations if a.get('test_engineer_name'))
    roles = get_unique_sorted(a.get('role') for a in all_allocations if a.get('role'))
    created_by_users = get_unique_sorted(a.get('created_by') for a in all_allocations if a.get('created_by'))
    
    return render_template('allocations/dashboard.html',
                         allocations=filtered_allocations,
                         stats=stats,
                         efficiency_data=efficiency_data,
                         user=user,
                         # Filter options
                         systems=systems,
                         categories=categories,
                         therapeutic_areas=therapeutic_areas,
                         test_engineers=test_engineers,
                         roles=roles,
                         created_by_users=created_by_users,
                         # Current filters
                         current_filters={
                             'system': filter_system,
                             'trial_category': filter_category,
                             'therapeutic_area': filter_therapeutic_area,
                             'test_engineer': filter_test_engineer,
                             'role': filter_role,
                             'trial_id': filter_trial_id,
                             'created_by': filter_created_by,
                             'start_date': filter_start_date,
                             'end_date': filter_end_date
                         })

# ============================================================================
# API ENDPOINTS (for AJAX and Charts)
# ============================================================================
@allocations_bp.route('/api/stats')
@login_required
def api_stats():
    """Get allocation statistics as JSON"""
    stats = get_allocation_statistics()
    return jsonify(stats)

@allocations_bp.route('/api/efficiency')
@login_required
@role_required('superuser', 'admin', 'manager')
def api_efficiency():
    """Get engineer efficiency data as JSON"""
    allocations = get_all_allocations()
    efficiency_data = calculate_engineer_efficiency(allocations)
    return jsonify(efficiency_data)

@allocations_bp.route('/api/filter', methods=['POST'])
@login_required
def api_filter():
    """Filter allocations via API"""
    filters = request.get_json()
    
    # Convert date strings to date objects if present
    if filters.get('start_date'):
        try:
            filters['start_date'] = datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
        except:
            pass
    
    if filters.get('end_date'):
        try:
            filters['end_date'] = datetime.strptime(filters['end_date'], '%Y-%m-%d').date()
        except:
            pass
    
    filtered = search_allocations(filters)
    
    user = session.get('user', {})
    role = user.get('role', '')
    
    # Filter by user if not admin/manager
    if role not in ['superuser', 'admin', 'manager']:
        username = user.get('username', '')
        filtered = [a for a in filtered if a.get('created_by') == username]
    
    return jsonify(filtered)

@allocations_bp.route('/api/chart-data/<chart_type>')
@login_required
@role_required('superuser', 'admin', 'manager')
def api_chart_data(chart_type):
    """Get chart data for dashboards with filters"""
    # Get filter parameters
    filter_system = request.args.get('system', '')
    filter_category = request.args.get('trial_category', '')
    filter_therapeutic_area = request.args.get('therapeutic_area', '')
    filter_test_engineer = request.args.get('test_engineer', '')
    filter_role = request.args.get('role', '')
    filter_trial_id = request.args.get('trial_id', '')
    filter_created_by = request.args.get('created_by', '')
    filter_start_date = request.args.get('start_date', '')
    filter_end_date = request.args.get('end_date', '')
    
    # Get all allocations
    allocations = get_all_allocations()
    
    # Apply filters (same logic as dashboard)
    if filter_system:
        allocations = [a for a in allocations if a.get('system') == filter_system]
    
    if filter_category:
        allocations = [a for a in allocations 
                      if a.get('trial_category_type') == filter_category or 
                      filter_category in a.get('trial_category', '')]
    
    if filter_therapeutic_area:
        allocations = [a for a in allocations 
                      if a.get('therapeutic_area_type') == filter_therapeutic_area or
                      filter_therapeutic_area in a.get('therapeutic_area', '')]
    
    if filter_test_engineer:
        allocations = [a for a in allocations 
                      if a.get('test_engineer_name') == filter_test_engineer]
    
    if filter_role:
        allocations = [a for a in allocations if a.get('role') == filter_role]
    
    if filter_trial_id:
        allocations = [a for a in allocations 
                      if filter_trial_id.lower() in a.get('trial_id', '').lower()]
    
    if filter_created_by:
        allocations = [a for a in allocations 
                      if a.get('created_by') == filter_created_by]
    
    if filter_start_date:
        try:
            start_date = datetime.strptime(filter_start_date, '%Y-%m-%d').date()
            allocations = [a for a in allocations 
                          if datetime.strptime(a.get('start_date', '2024-01-01'), '%Y-%m-%d').date() >= start_date]
        except:
            pass
    
    if filter_end_date:
        try:
            end_date = datetime.strptime(filter_end_date, '%Y-%m-%d').date()
            allocations = [a for a in allocations 
                          if datetime.strptime(a.get('end_date', '2024-12-31'), '%Y-%m-%d').date() <= end_date]
        except:
            pass
    
    # Generate chart data based on filtered allocations
    if chart_type == 'system':
        data = {}
        for a in allocations:
            system = a.get('system', 'Unknown')
            data[system] = data.get(system, 0) + 1
        return jsonify({'labels': list(data.keys()), 'values': list(data.values())})
    
    elif chart_type == 'category':
        data = {'Build': 0, 'Change Request': 0}
        for a in allocations:
            cat_type = a.get('trial_category_type', 'Build')
            if not cat_type:
                cat_type = 'Change Request' if 'Change Request' in a.get('trial_category', '') else 'Build'
            data[cat_type] = data.get(cat_type, 0) + 1
        return jsonify({'labels': list(data.keys()), 'values': list(data.values())})
    
    elif chart_type == 'therapeutic_area':
        data = {}
        for a in allocations:
            area_type = a.get('therapeutic_area_type', 'Unknown')
            if not area_type:
                area = a.get('therapeutic_area', 'Unknown')
                area_type = 'Others' if 'Others -' in area else area
            data[area_type] = data.get(area_type, 0) + 1
        return jsonify({'labels': list(data.keys()), 'values': list(data.values())})
    
    elif chart_type == 'engineer_workload':
        data = {}
        for a in allocations:
            engineer = a.get('test_engineer_name', 'Unknown')
            data[engineer] = data.get(engineer, 0) + 1
        sorted_data = dict(sorted(data.items(), key=lambda x: x[1], reverse=True)[:10])
        return jsonify({'labels': list(sorted_data.keys()), 'values': list(sorted_data.values())})
    
    elif chart_type == 'monthly':
        data = {}
        for a in allocations:
            try:
                start = datetime.strptime(a.get('start_date', '2024-01-01'), '%Y-%m-%d')
                month_key = start.strftime('%Y-%m')
                data[month_key] = data.get(month_key, 0) + 1
            except:
                pass
        sorted_data = dict(sorted(data.items()))
        return jsonify({'labels': list(sorted_data.keys()), 'values': list(sorted_data.values())})
    
    else:
        return jsonify({'error': 'Invalid chart type'}), 400

@allocations_bp.route('/export/excel')
@login_required
def export_excel():
    """Export allocations to Excel"""
    user = session.get('user', {})
    role = user.get('role', '')
    username = user.get('username', '')
    
    # Get allocations based on role
    allocations = get_allocations_by_role(role, username)
    
    if not allocations:
        flash('No allocations to export', 'warning')
        return redirect(url_for('allocations.list_view'))
    
    try:
        # Check if pandas is available
        try:
            import pandas as pd  # type: ignore
            from io import BytesIO
        except ImportError:
            flash('Excel export requires pandas. Please install: pip install pandas openpyxl', 'danger')
            return redirect(url_for('allocations.list_view'))
        
        # Create DataFrame
        df = pd.DataFrame(allocations)
        
        # Select and order columns
        columns = ['trial_id', 'test_engineer_name', 'system', 'trial_category', 
                  'therapeutic_area', 'role', 'activity', 'start_date', 'end_date', 
                  'created_by', 'created_at']
        
        available_columns = [col for col in columns if col in df.columns]
        df_export = df[available_columns]
        
        # Create Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Allocations')
        
        output.seek(0)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if role in ['superuser', 'admin', 'manager']:
            filename = f'all_allocations_{timestamp}.xlsx'
        else:
            filename = f'allocations_{username}_{timestamp}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        flash(f'Error exporting to Excel: {str(e)}', 'danger')
        return redirect(url_for('allocations.list_view'))