"""
Audit Blueprint - Trail Audit Documents Management
Handles trail audit documents recording by users
Session-based authentication with role-based access
✅ WITH AUDIT REVIEWER ACCESS
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from functools import wraps
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Set

from services.audit_service import (
    get_all_trail_documents,
    get_trail_document_by_id,
    create_trail_document as service_create_trail_document,
    update_trail_document as service_update_trail_document,
    delete_trail_document as service_delete_trail_document,
    check_duplicate_tmf_vault_id
)

# Create Blueprint
audit_bp = Blueprint('audit', __name__, url_prefix='/audit')

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


def audit_reviewer_required(f):
    """Decorator to require audit reviewer access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        user = session.get('user', {})
        is_reviewer = user.get('is_audit_reviewer', False)
        is_superuser = user.get('role') == 'superuser'
        
        if not is_reviewer and not is_superuser:
            flash('❌ Access Denied: Audit Reviewer access required', 'danger')
            return redirect(url_for('home.index'))
        
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_unique_sorted_values(items: List[Dict[str, Any]], key: str) -> List[str]:
    """
    Extract unique non-None values from a list of dictionaries and return sorted list.
    
    Args:
        items: List of dictionaries
        key: The key to extract values from
    
    Returns:
        Sorted list of unique non-None string values
    """
    unique_values: Set[str] = set()
    for item in items:
        value = item.get(key)
        if value is not None and value != "":
            unique_values.add(str(value))
    return sorted(unique_values)


# ============================================================================
# MAIN ROUTES
# ============================================================================

@audit_bp.route('/')
@audit_bp.route('/main')
@login_required
def main():
    """Audit main page - redirect to trail documents"""
    return redirect(url_for('audit.trail_documents'))


# ============================================================================
# TRAIL DOCUMENTS ROUTES (REGULAR USERS)
# ============================================================================

@audit_bp.route('/trail-documents')
@login_required
def trail_documents():
    """Trail audit documents main page"""
    user = session.get('user', {})
    role = user.get('role', 'user')
    username = user.get('username', '')
    is_reviewer = user.get('is_audit_reviewer', False)
    
    # Get all documents
    all_documents = get_all_trail_documents()
    
    # Filter based on role
    if role in ['superuser', 'admin', 'manager']:
        documents = all_documents
    else:
        documents = [d for d in all_documents if d.get('created_by') == username]
    
    # Calculate statistics
    stats = {
        'total': len(documents),
        'te_docs': len([d for d in documents if d.get('te_document') == 'Yes']),
        'build': len([d for d in documents if d.get('category') == 'Build']),
        'change_request': len([d for d in documents if d.get('category') == 'Change Request'])
    }
    
    # Get unique values for filters
    trails = get_unique_sorted_values(documents, 'trail')
    uat_rounds = get_unique_sorted_values(documents, 'uat_round')
    tmf_ids = get_unique_sorted_values(documents, 'tmf_vault_id')
    
    return render_template('audit/trail_documents.html',
                         documents=documents,
                         stats=stats,
                         trails=trails,
                         uat_rounds=uat_rounds,
                         tmf_ids=tmf_ids,
                         user=user,
                         is_reviewer=is_reviewer)


@audit_bp.route('/trail-documents/create', methods=['GET', 'POST'])
@login_required
def create_trail_document():
    """Create new trail document"""
    user = session.get('user', {})
    username = user.get('username', '')
    
    if request.method == 'POST':
        try:
            data = request.form.to_dict()
            
            # Debug: Print received data
            print("="*60)
            print("RECEIVED FORM DATA:")
            for key, value in data.items():
                print(f"  {key}: {value}")
            print("="*60)
            
            # Check for duplicate TMF/Vault ID
            tmf_vault_id = data.get('tmf_vault_id', '').strip()
            if tmf_vault_id:
                is_duplicate, dup_info = check_duplicate_tmf_vault_id(tmf_vault_id)
                if is_duplicate:
                    flash(f'❌ TMF/Vault ID already exists in Trail: {dup_info.get("trail")}', 'danger')
                    return render_template('audit/trail_document_form.html',
                                         form_data=data,
                                         user=user,
                                         action='create')
            
            # Validate required fields
            required = ['trail', 'category', 'te1', 'te2', 'document_name', 
                       'te_document', 'uat_round', 'tmf_vault_id', 'go_live_date']
            
            missing_fields = []
            for field in required:
                if not data.get(field):
                    missing_fields.append(field)
            
            if missing_fields:
                flash(f'❌ Missing required fields: {", ".join(missing_fields)}', 'danger')
                return render_template('audit/trail_document_form.html',
                                     form_data=data,
                                     user=user,
                                     action='create')
            
            # Validate conditional fields
            te_document = data.get('te_document')
            if te_document == 'Yes':
                if not data.get('te1_approval_date') or not data.get('te2_approval_date'):
                    flash('❌ TE1 and TE2 Approval dates required when TE Document = Yes', 'danger')
                    return render_template('audit/trail_document_form.html',
                                         form_data=data,
                                         user=user,
                                         action='create')
            else:
                if not data.get('ctdm_approval_date'):
                    flash('❌ CTDM Approval date required when TE Document = No', 'danger')
                    return render_template('audit/trail_document_form.html',
                                         form_data=data,
                                         user=user,
                                         action='create')
            
            # Create document using service function
            data['created_by'] = username
            success, message = service_create_trail_document(data)
            
            if success:
                flash(f'✅ Trail document created successfully! TMF/Vault ID: {tmf_vault_id}', 'success')
                return redirect(url_for('audit.trail_documents'))
            else:
                flash(message, 'danger')
                return render_template('audit/trail_document_form.html',
                                     form_data=data,
                                     user=user,
                                     action='create')
        
        except Exception as e:
            print("="*60)
            print(f"ERROR CREATING DOCUMENT: {str(e)}")
            import traceback
            traceback.print_exc()
            print("="*60)
            flash(f'❌ Error creating document: {str(e)}', 'danger')
            return render_template('audit/trail_document_form.html',
                                 form_data=request.form.to_dict(),
                                 user=user,
                                 action='create')
    
    return render_template('audit/trail_document_form.html',
                         user=user,
                         action='create')


@audit_bp.route('/trail-documents/edit/<document_id>', methods=['GET', 'POST'])
@login_required
def edit_trail_document(document_id):
    """Edit trail document"""
    user = session.get('user', {})
    role = user.get('role', 'user')
    username = user.get('username', '')
    
    document = get_trail_document_by_id(document_id)
    
    if not document:
        flash('❌ Document not found', 'danger')
        return redirect(url_for('audit.trail_documents'))
    
    # Check permissions
    if role not in ['superuser', 'admin', 'manager']:
        if document.get('created_by') != username:
            flash('❌ You do not have permission to edit this document', 'danger')
            return redirect(url_for('audit.trail_documents'))
    
    if request.method == 'POST':
        try:
            data = request.form.to_dict()
            
            # Check for duplicate TMF/Vault ID (excluding current document)
            tmf_vault_id = data.get('tmf_vault_id', '').strip()
            if tmf_vault_id:
                is_duplicate, dup_info = check_duplicate_tmf_vault_id(tmf_vault_id, exclude_id=document_id)
                if is_duplicate:
                    flash(f'❌ TMF/Vault ID already exists in Trail: {dup_info.get("trail")}', 'danger')
                    return render_template('audit/trail_document_form.html',
                                         document=document,
                                         form_data=data,
                                         user=user,
                                         action='edit')
            
            data['updated_by'] = username
            success, message = service_update_trail_document(document_id, data)
            
            if success:
                flash('✅ Trail document updated successfully!', 'success')
                return redirect(url_for('audit.trail_documents'))
            else:
                flash(message, 'danger')
                return render_template('audit/trail_document_form.html',
                                     document=document,
                                     form_data=data,
                                     user=user,
                                     action='edit')
        
        except Exception as e:
            print(f"ERROR UPDATING DOCUMENT: {str(e)}")
            flash(f'❌ Error updating document: {str(e)}', 'danger')
            return render_template('audit/trail_document_form.html',
                                 document=document,
                                 form_data=request.form.to_dict(),
                                 user=user,
                                 action='edit')
    
    return render_template('audit/trail_document_form.html',
                         document=document,
                         user=user,
                         action='edit')


@audit_bp.route('/trail-documents/delete/<document_id>', methods=['POST'])
@login_required
def delete_trail_document(document_id):
    """Delete trail document"""
    user = session.get('user', {})
    role = user.get('role', 'user')
    username = user.get('username', '')
    
    document = get_trail_document_by_id(document_id)
    
    if not document:
        flash('❌ Document not found', 'danger')
        return redirect(url_for('audit.trail_documents'))
    
    # Check permissions
    if role not in ['superuser', 'admin']:
        if document.get('created_by') != username:
            flash('❌ You do not have permission to delete this document', 'danger')
            return redirect(url_for('audit.trail_documents'))
    
    success, message = service_delete_trail_document(document_id)
    
    if success:
        flash('✅ Trail document deleted successfully', 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('audit.trail_documents'))


@audit_bp.route('/trail-documents/check-duplicate', methods=['POST'])
@login_required
def check_duplicate_tmf():
    """API endpoint to check for duplicate TMF/Vault ID"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'is_duplicate': False, 'error': 'No data provided'})
        
        tmf_vault_id = data.get('tmf_vault_id', '').strip()
        exclude_id = data.get('exclude_id')
        
        if not tmf_vault_id:
            return jsonify({'is_duplicate': False})
        
        is_duplicate, dup_info = check_duplicate_tmf_vault_id(tmf_vault_id, exclude_id)
        
        return jsonify({
            'is_duplicate': is_duplicate,
            'duplicate_info': dup_info if is_duplicate else None
        })
    
    except Exception as e:
        print(f"ERROR in check_duplicate_tmf: {str(e)}")
        return jsonify({'is_duplicate': False, 'error': str(e)})


@audit_bp.route('/trail-documents/export')
@login_required
@role_required('superuser', 'admin')
def export_trail_documents():
    """Export trail documents to Excel"""
    try:
        import pandas as pd
        
        documents = get_all_trail_documents()
        
        if not documents:
            flash('⚠️ No documents to export', 'warning')
            return redirect(url_for('audit.trail_documents'))
        
        # Prepare data
        excel_data = []
        for doc in documents:
            category_display = doc.get('category', 'N/A')
            if doc.get('cr_number'):
                category_display = f"{category_display} - {doc.get('cr_number')}"
            
            excel_data.append({
                'Trail': doc.get('trail'),
                'TE1': doc.get('te1'),
                'TE2': doc.get('te2'),
                'Document Name': doc.get('document_name'),
                'Category': category_display,
                'TE Document': doc.get('te_document'),
                'UAT Round': doc.get('uat_round'),
                'TMF/Vault ID': doc.get('tmf_vault_id'),
                'TE1 Approval': doc.get('te1_approval_date', 'N/A'),
                'TE2 Approval': doc.get('te2_approval_date', 'N/A'),
                'CTDM Approval': doc.get('ctdm_approval_date', 'N/A'),
                'Go Live Date': doc.get('go_live_date'),
                'Created By': doc.get('created_by'),
                'Created At': doc.get('created_at')
            })
        
        df = pd.DataFrame(excel_data)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Trail Documents')
        
        output.seek(0)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'trail_documents_{timestamp}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    
    except ImportError:
        flash('❌ Excel export requires pandas. Please install: pip install pandas openpyxl', 'danger')
        return redirect(url_for('audit.trail_documents'))
    except Exception as e:
        flash(f'❌ Error exporting: {str(e)}', 'danger')
        return redirect(url_for('audit.trail_documents'))


# ============================================================================
# AUDIT REVIEWER ROUTES (READ-ONLY ACCESS TO ALL DOCUMENTS)
# ============================================================================

@audit_bp.route('/reviewer/all-documents')
@login_required
@audit_reviewer_required
def reviewer_all_documents():
    """
    Audit Reviewer View - ALL trail documents (READ-ONLY)
    Only accessible by users with is_audit_reviewer = True or superuser
    """
    user = session.get('user', {})
    username = user.get('username', '')
    
    # Get ALL documents (no filtering by creator)
    all_documents = get_all_trail_documents()
    
    # Apply filters from query parameters
    trail_filter = request.args.get('trail', 'All')
    category_filter = request.args.get('category', 'All')
    uat_filter = request.args.get('uat_round', 'All')
    tmf_filter = request.args.get('tmf_vault_id', 'All')
    created_by_filter = request.args.get('created_by', 'All')
    
    # Filter documents
    filtered_docs = all_documents
    if trail_filter != 'All':
        filtered_docs = [d for d in filtered_docs if d.get('trail') == trail_filter]
    if category_filter != 'All':
        filtered_docs = [d for d in filtered_docs if d.get('category') == category_filter]
    if uat_filter != 'All':
        filtered_docs = [d for d in filtered_docs if d.get('uat_round') == uat_filter]
    if tmf_filter != 'All':
        filtered_docs = [d for d in filtered_docs if d.get('tmf_vault_id') == tmf_filter]
    if created_by_filter != 'All':
        filtered_docs = [d for d in filtered_docs if d.get('created_by') == created_by_filter]
    
    # Calculate statistics
    stats = {
        'total': len(filtered_docs),
        'te_docs': len([d for d in filtered_docs if d.get('te_document') == 'Yes']),
        'build': len([d for d in filtered_docs if d.get('category') == 'Build']),
        'change_request': len([d for d in filtered_docs if d.get('category') == 'Change Request'])
    }
    
    # Get unique values for filters (from all documents)
    trails = get_unique_sorted_values(all_documents, 'trail')
    uat_rounds = get_unique_sorted_values(all_documents, 'uat_round')
    tmf_ids = get_unique_sorted_values(all_documents, 'tmf_vault_id')
    created_by_list = get_unique_sorted_values(all_documents, 'created_by')
    
    return render_template('audit/reviewer_documents.html',
                         documents=filtered_docs,
                         stats=stats,
                         trails=trails,
                         uat_rounds=uat_rounds,
                         tmf_ids=tmf_ids,
                         created_by_list=created_by_list,
                         user=user,
                         read_only=True,
                         filters={
                             'trail': trail_filter,
                             'category': category_filter,
                             'uat_round': uat_filter,
                             'tmf_vault_id': tmf_filter,
                             'created_by': created_by_filter
                         })


@audit_bp.route('/reviewer/view/<document_id>')
@login_required
@audit_reviewer_required
def reviewer_view_document(document_id):
    """
    View single document (READ-ONLY for audit reviewers)
    """
    user = session.get('user', {})
    
    document = get_trail_document_by_id(document_id)
    
    if not document:
        flash('❌ Document not found', 'danger')
        return redirect(url_for('audit.reviewer_all_documents'))
    
    return render_template('audit/reviewer_view_document.html',
                         document=document,
                         user=user,
                         read_only=True)


@audit_bp.route('/reviewer/export')
@login_required
@audit_reviewer_required
def reviewer_export_documents():
    """
    Export ALL trail documents to Excel (Audit Reviewer)
    Audit reviewers can download all documents
    """
    try:
        import pandas as pd
        
        # Get ALL documents
        documents = get_all_trail_documents()
        
        if not documents:
            flash('⚠️ No documents to export', 'warning')
            return redirect(url_for('audit.reviewer_all_documents'))
        
        # Apply filters from query parameters
        trail_filter = request.args.get('trail')
        category_filter = request.args.get('category')
        uat_filter = request.args.get('uat_round')
        tmf_filter = request.args.get('tmf_vault_id')
        created_by_filter = request.args.get('created_by')
        
        # Filter documents
        filtered_docs = documents
        if trail_filter and trail_filter != 'All':
            filtered_docs = [d for d in filtered_docs if d.get('trail') == trail_filter]
        if category_filter and category_filter != 'All':
            filtered_docs = [d for d in filtered_docs if d.get('category') == category_filter]
        if uat_filter and uat_filter != 'All':
            filtered_docs = [d for d in filtered_docs if d.get('uat_round') == uat_filter]
        if tmf_filter and tmf_filter != 'All':
            filtered_docs = [d for d in filtered_docs if d.get('tmf_vault_id') == tmf_filter]
        if created_by_filter and created_by_filter != 'All':
            filtered_docs = [d for d in filtered_docs if d.get('created_by') == created_by_filter]
        
        # Prepare data for Excel
        excel_data = []
        for doc in filtered_docs:
            category_display = doc.get('category', 'N/A')
            if doc.get('cr_number'):
                category_display = f"{category_display} - {doc.get('cr_number')}"
            
            excel_data.append({
                'Trail': doc.get('trail'),
                'TE1': doc.get('te1'),
                'TE2': doc.get('te2'),
                'Document Name': doc.get('document_name'),
                'Category': category_display,
                'TE Document': doc.get('te_document'),
                'UAT Round': doc.get('uat_round'),
                'TMF/Vault ID': doc.get('tmf_vault_id'),
                'TE1 Approval': doc.get('te1_approval_date', 'N/A'),
                'TE2 Approval': doc.get('te2_approval_date', 'N/A'),
                'CTDM Approval': doc.get('ctdm_approval_date', 'N/A'),
                'Go Live Date': doc.get('go_live_date'),
                'Created By': doc.get('created_by'),
                'Created At': doc.get('created_at')
            })
        
        df = pd.DataFrame(excel_data)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Audit Trail Documents')
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Audit Trail Documents']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                ) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
        
        output.seek(0)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'audit_trail_documents_{timestamp}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    
    except ImportError:
        flash('❌ Excel export requires pandas. Please install: pip install pandas openpyxl', 'danger')
        return redirect(url_for('audit.reviewer_all_documents'))
    except Exception as e:
        flash(f'❌ Error exporting: {str(e)}', 'danger')
        return redirect(url_for('audit.reviewer_all_documents'))


@audit_bp.route('/reviewer/request-access', methods=['POST'])
@login_required
def request_reviewer_access():
    """
    Request audit reviewer access (for existing users)
    """
    from services.user_service import request_audit_reviewer_access
    
    user = session.get('user', {})
    username = user.get('username', '')
    justification = request.form.get('justification', '').strip()
    
    if not justification:
        flash('⚠️ Please provide justification for Audit Reviewer access', 'danger')
        return redirect(url_for('audit.trail_documents'))
    
    success, message = request_audit_reviewer_access(username, justification)
    
    if success:
        flash(f'✅ {message}', 'success')
        flash('ℹ️ Your request has been submitted to the Super User for approval', 'info')
    else:
        flash(f'❌ {message}', 'danger')
    
    return redirect(url_for('audit.trail_documents'))

