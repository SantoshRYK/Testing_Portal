"""
Quality Blueprint - Complete Implementation
Handles all quality-related routes including wizard flow
Session-based authentication with therapeutic area and auto-round tracking
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
from services.quality_service import (
    create_record,
    get_all_records,
    get_record_by_id,
    get_records_by_user,
    update_record,
    delete_record,
    get_unique_values,
    get_statistics,
    get_requirement_round  # New function for auto-round calculation
)

quality_bp = Blueprint('quality', __name__, url_prefix='/quality')

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
@quality_bp.route('/')
@quality_bp.route('/main')
@login_required
def main():
    """Quality main page - router based on role"""
    user = session.get('user', {})
    role = user.get('role', 'user')
    
    # Manager goes to dashboard
    if role == 'manager':
        return redirect(url_for('quality.dashboard'))
    else:
        # Regular users go to create landing
        return render_template('quality/main.html', user=user)

@quality_bp.route('/dashboard')
@login_required
def dashboard():
    """Quality dashboard with charts and metrics"""
    user = session.get('user', {})
    role = user.get('role', 'user')
    username = user.get('username', '')
    
    # Get filter parameters
    trial_id = request.args.get('trial_id', 'All')
    phase = request.args.get('phase', 'All')
    req_type = request.args.get('type', 'All')
    round_num = request.args.get('round', 'All')
    
    # Build filters
    filters = {}
    if trial_id != 'All':
        filters['trial_id'] = trial_id
    if phase != 'All':
        filters['phase'] = phase
    if req_type != 'All':
        filters['type_of_requirement'] = req_type
    if round_num != 'All':
        filters['current_round'] = int(round_num)
    
    # Get statistics
    stats = get_statistics(filters if filters else None)
    
    # Get filter options
    trial_ids = get_unique_values('trial_id')
    phases = get_unique_values('phase')
    types = get_unique_values('type_of_requirement')
    rounds = get_unique_values('current_round')
    
    # Get filtered records for table
    if role == 'user':
        all_records = get_records_by_user(username)
    else:
        all_records = get_all_records()
    
    # Apply filters to records
    filtered_records = all_records
    for key, value in filters.items():
        filtered_records = [r for r in filtered_records if str(r.get(key)) == str(value)]
    
    return render_template('quality/dashboard.html',
                         stats=stats,
                         records=filtered_records,
                         trial_ids=trial_ids,
                         phases=phases,
                         types=types,
                         rounds=rounds,
                         filters={'trial_id': trial_id, 'phase': phase, 'type': req_type, 'round': round_num},
                         user=user)

@quality_bp.route('/create', methods=['GET'])
@login_required
def create():
    """Create landing page - shows start wizard button"""
    user = session.get('user', {})
    username = user.get('username', '')
    
    # Get user's recent records
    recent_records = get_records_by_user(username)
    recent_records = sorted(recent_records, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
    
    return render_template('quality/create.html', recent_records=recent_records, user=user)

@quality_bp.route('/wizard/trial-setup', methods=['GET', 'POST'])
@login_required
def trial_setup():
    """Wizard Step 1: Trial Setup"""
    user = session.get('user', {})
    
    if request.method == 'POST':
        # Validate and save trial data to session
        trial_id = request.form.get('trial_id', '').strip()
        phase = request.form.get('phase', '').strip()
        phase_other = request.form.get('phase_other', '').strip()
        therapeutic_area = request.form.get('therapeutic_area', '').strip()
        therapeutic_area_other = request.form.get('therapeutic_area_other', '').strip()
        no_of_rounds = request.form.get('no_of_rounds', '').strip()
        
        # Use "Other" input if selected
        if phase == 'Other' and phase_other:
            phase = phase_other
        
        # Handle therapeutic area "Others"
        if therapeutic_area == 'Others' and therapeutic_area_other:
            therapeutic_area = f"Others - {therapeutic_area_other}"
        
        # Validation
        if not trial_id or not phase or not therapeutic_area or not no_of_rounds:
            flash('All fields are required', 'danger')
            return render_template('quality/trial_setup.html', user=user)
        
        try:
            rounds_int = int(no_of_rounds)
            if rounds_int <= 0:
                flash('Number of rounds must be greater than 0', 'danger')
                return render_template('quality/trial_setup.html', user=user)
        except ValueError:
            flash('Number of rounds must be a valid number', 'danger')
            return render_template('quality/trial_setup.html', user=user)
        
        # Save to session
        session['wizard_trial_data'] = {
            'trial_id': trial_id,
            'phase': phase,
            'therapeutic_area': therapeutic_area,
            'no_of_rounds': int(no_of_rounds)
        }
        session['wizard_records'] = []
        
        flash('Trial information saved! Proceed to record entry.', 'success')
        return redirect(url_for('quality.record_entry'))
    
    return render_template('quality/trial_setup.html', user=user)

@quality_bp.route('/wizard/record-entry', methods=['GET', 'POST'])
@login_required
def record_entry():
    """Wizard Step 2: Record Entry"""
    user = session.get('user', {})
    username = user.get('username', '')
    
    # Check if trial data exists
    if 'wizard_trial_data' not in session:
        flash('No trial data found. Please start from Trial Setup.', 'warning')
        return redirect(url_for('quality.trial_setup'))
    
    trial_data = session['wizard_trial_data']
    wizard_records = session.get('wizard_records', [])
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_record':
            # Add record to wizard list
            try:
                type_of_requirement = request.form.get('type_of_requirement', '').strip()
                
                # Validate requirement type first
                if not type_of_requirement:
                    flash('Type of requirement is required', 'danger')
                    return render_template('quality/record_entry.html',
                                         trial_data=trial_data,
                                         wizard_records=wizard_records,
                                         user=user)
                
                current_round = int(request.form.get('current_round', 1))
                
                record = {
                    'type_of_requirement': type_of_requirement,
                    'current_round': current_round,
                    'total_requirements': int(request.form.get('total_requirements', 0)),
                    'total_failures': int(request.form.get('total_failures', 0)),
                    'spec_issue': int(request.form.get('spec_issue', 0)),
                    'mock_crf_issue': int(request.form.get('mock_crf_issue', 0)),
                    'programming_issue': int(request.form.get('programming_issue', 0)),
                    'scripting_issue': int(request.form.get('scripting_issue', 0)),
                    'documentation_issues': request.form.get('documentation_issues', '').strip(),
                    'timeline_adherence': request.form.get('timeline_adherence', '').strip(),
                    'system_deployment_delays': request.form.get('system_deployment_delays', '').strip()
                }
                
                # Validation
                if record['total_requirements'] <= 0:
                    flash('Total Requirements must be greater than 0', 'danger')
                elif record['total_failures'] > record['total_requirements']:
                    flash('Total Failures cannot exceed Total Requirements', 'danger')
                else:
                    failure_sum = (record['spec_issue'] + record['mock_crf_issue'] + 
                                 record['programming_issue'] + record['scripting_issue'])
                    if failure_sum > record['total_failures']:
                        flash(f'Sum of failure reasons ({failure_sum}) cannot exceed total failures', 'danger')
                    else:
                        # Calculate requirement round (auto-increment per type)
                        req_round = get_requirement_round(
                            trial_data['trial_id'],
                            type_of_requirement,  # Now safe - validated above
                            wizard_records
                        )
                        record['requirement_round'] = req_round
                        
                        wizard_records.append(record)
                        session['wizard_records'] = wizard_records
                        flash(f'✅ Record added! Total: {len(wizard_records)} | {type_of_requirement} Requirement Round: {req_round}', 'success')
                        return redirect(url_for('quality.record_entry'))
                
            except ValueError:
                flash('Invalid numeric value', 'danger')
        
        elif action == 'save_all':
            # Save all records
            success_count = 0
            error_count = 0
            
            for record in wizard_records:
                # Merge trial data with record
                full_record = {**trial_data, **record}
                success, message = create_record(full_record, username)
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    flash(message, 'danger')
            
            if success_count > 0:
                flash(f'✅ Successfully saved {success_count} record(s)!', 'success')
                # Clear wizard state
                session.pop('wizard_trial_data', None)
                session.pop('wizard_records', None)
                return redirect(url_for('quality.view_records'))
            
            if error_count > 0:
                flash(f'❌ Failed to save {error_count} record(s)', 'danger')
        
        elif action == 'remove_record':
            idx = int(request.form.get('record_index', -1))
            if 0 <= idx < len(wizard_records):
                wizard_records.pop(idx)
                session['wizard_records'] = wizard_records
                flash('Record removed', 'info')
                return redirect(url_for('quality.record_entry'))
    
    return render_template('quality/record_entry.html',
                         trial_data=trial_data,
                         wizard_records=wizard_records,
                         user=user)

@quality_bp.route('/records')
@login_required
def view_records():
    """View quality records list"""
    user = session.get('user', {})
    role = user.get('role', 'user')
    username = user.get('username', '')
    
    # Get filter parameters
    trial_id = request.args.get('trial_id', 'All')
    phase = request.args.get('phase', 'All')
    req_type = request.args.get('type', 'All')
    
    # Get records based on role
    if role == 'user':
        records = get_records_by_user(username)
    else:
        records = get_all_records()
    
    # Apply filters
    if trial_id != 'All':
        records = [r for r in records if r.get('trial_id') == trial_id]
    if phase != 'All':
        records = [r for r in records if r.get('phase') == phase]
    if req_type != 'All':
        records = [r for r in records if r.get('type_of_requirement') == req_type]
    
    # Get filter options
    trial_ids = get_unique_values('trial_id')
    phases = get_unique_values('phase')
    types = get_unique_values('type_of_requirement')
    
    return render_template('quality/view.html',
                         records=records,
                         trial_ids=trial_ids,
                         phases=phases,
                         types=types,
                         filters={'trial_id': trial_id, 'phase': phase, 'type': req_type},
                         user=user)

@quality_bp.route('/view/<record_id>')
@login_required
def view_single(record_id):
    """View single quality record detail"""
    user = session.get('user', {})
    role = user.get('role', 'user')
    username = user.get('username', '')
    
    record = get_record_by_id(record_id)
    
    if not record:
        flash('Quality record not found', 'danger')
        return redirect(url_for('quality.view_records'))
    
    # Check permissions
    if role not in ['superuser', 'admin', 'manager']:
        if record.get('created_by') != username:
            flash('You do not have permission to view this record', 'danger')
            return redirect(url_for('quality.view_records'))
    
    return render_template('quality/view_single.html', record=record, user=user)

@quality_bp.route('/edit/<record_id>', methods=['GET', 'POST'])
@login_required
def edit(record_id):
    """Edit quality record"""
    user = session.get('user', {})
    role = user.get('role', 'user')
    username = user.get('username', '')
    
    record = get_record_by_id(record_id)
    
    if not record:
        flash('Quality record not found', 'danger')
        return redirect(url_for('quality.view_records'))
    
    # Check permissions
    if role not in ['superuser', 'admin', 'manager']:
        if record.get('created_by') != username:
            flash('You do not have permission to edit this record', 'danger')
            return redirect(url_for('quality.view_records'))
    
    if request.method == 'POST':
        try:
            updates = {
                'trial_id': request.form.get('trial_id', '').strip(),
                'phase': request.form.get('phase', '').strip(),
                'therapeutic_area': request.form.get('therapeutic_area', '').strip(),
                'no_of_rounds': int(request.form.get('no_of_rounds', 0)),
                'type_of_requirement': request.form.get('type_of_requirement'),
                'current_round': int(request.form.get('current_round', 1)),
                'total_requirements': int(request.form.get('total_requirements', 0)),
                'total_failures': int(request.form.get('total_failures', 0)),
                'spec_issue': int(request.form.get('spec_issue', 0)),
                'mock_crf_issue': int(request.form.get('mock_crf_issue', 0)),
                'programming_issue': int(request.form.get('programming_issue', 0)),
                'scripting_issue': int(request.form.get('scripting_issue', 0)),
                'documentation_issues': request.form.get('documentation_issues', '').strip(),
                'timeline_adherence': request.form.get('timeline_adherence', '').strip(),
                'system_deployment_delays': request.form.get('system_deployment_delays', '').strip()
            }
            
            success, message = update_record(record_id, updates, username)
            
            if success:
                flash(message, 'success')
                return redirect(url_for('quality.view_single', record_id=record_id))
            else:
                flash(message, 'danger')
                
        except ValueError:
            flash('Invalid numeric value', 'danger')
    
    # Get phase options
    phase_options = ["Phase 1 & NIS", "Phase 2", "Phase 3", "Other"]
    
    # Get therapeutic area options
    therapeutic_areas = ["Cardio-Metabolic", "Rare Disease", "Obesity", "Haemophilia", "Growth Disorders", "Others"]
    
    return render_template('quality/edit.html', 
                         record=record,
                         phase_options=phase_options,
                         therapeutic_areas=therapeutic_areas,
                         user=user)

@quality_bp.route('/delete/<record_id>', methods=['POST'])
@login_required
def delete_route(record_id):
    """Delete quality record"""
    user = session.get('user', {})
    role = user.get('role', 'user')
    username = user.get('username', '')
    
    record = get_record_by_id(record_id)
    
    if not record:
        flash('Quality record not found', 'danger')
        return redirect(url_for('quality.view_records'))
    
    # Check permissions
    if role not in ['superuser', 'admin']:
        if record.get('created_by') != username:
            flash('You do not have permission to delete this record', 'danger')
            return redirect(url_for('quality.view_records'))
    
    success, message = delete_record(record_id, username)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('quality.view_records'))

@quality_bp.route('/wizard/clear')
@login_required
def clear_wizard():
    """Clear wizard state"""
    session.pop('wizard_trial_data', None)
    session.pop('wizard_records', None)
    flash('Wizard cleared', 'info')
    return redirect(url_for('quality.main'))

# ============================================================================
# API ENDPOINTS
# ============================================================================
@quality_bp.route('/api/statistics')
@login_required
def api_statistics():
    """API endpoint for dashboard statistics"""
    filters = {}
    
    if request.args.get('trial_id') and request.args.get('trial_id') != 'All':
        filters['trial_id'] = request.args.get('trial_id')
    if request.args.get('phase') and request.args.get('phase') != 'All':
        filters['phase'] = request.args.get('phase')
    if request.args.get('type') and request.args.get('type') != 'All':
        filters['type_of_requirement'] = request.args.get('type')
    
    stats = get_statistics(filters if filters else None)
    return jsonify(stats)

@quality_bp.route('/api/records')
@login_required
def api_records():
    """API endpoint for records list"""
    user = session.get('user', {})
    role = user.get('role', 'user')
    username = user.get('username', '')
    
    if role == 'user':
        records = get_records_by_user(username)
    else:
        records = get_all_records()
    
    return jsonify(records)