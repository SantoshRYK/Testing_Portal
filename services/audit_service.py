"""
Audit Service - Trail Documents and Audit Logging
"""
import uuid
from datetime import datetime
from typing import List, Dict, Any
from utils.database import load_data, save_data

# ============================================================================
# AUDIT LOGGING FUNCTIONS
# ============================================================================
def log_audit(username, action, category, entity_type, entity_id, details=None):
    """Log audit event"""
    audit_logs = load_data('audit_logs')
    
    log_entry = {
        'id': str(uuid.uuid4()),
        'username': username,
        'action': action,
        'category': category,
        'entity_type': entity_type,
        'entity_id': entity_id,
        'details': details or {},
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    audit_logs.append(log_entry)
    save_data('audit_logs', audit_logs)
    return True

def get_audit_logs():
    """Get all audit logs"""
    return load_data('audit_logs')

def get_audit_statistics():
    """Get audit statistics"""
    logs = get_audit_logs()
    documents = get_all_trail_documents()
    
    return {
        'total_logs': len(logs),
        'total_documents': len(documents),
        'unique_users': len(set(log.get('username') for log in logs if log.get('username'))),
        'recent_actions': len([log for log in logs if log.get('timestamp', '').startswith(datetime.now().strftime('%Y-%m-%d'))])
    }

# ============================================================================
# TRAIL DOCUMENTS FUNCTIONS
# ============================================================================
def get_all_trail_documents():
    """Get all trail documents"""
    return load_data('trail_documents')

def get_trail_document_by_id(document_id):
    """Get trail document by ID"""
    documents = load_data('trail_documents')
    return next((d for d in documents if d.get('id') == document_id), None)

def check_duplicate_tmf_vault_id(tmf_vault_id, exclude_id=None):
    """
    Check if TMF/Vault ID already exists
    Returns: (is_duplicate, duplicate_document_info)
    """
    if not tmf_vault_id or not tmf_vault_id.strip():
        return False, {}
    
    documents = load_data('trail_documents')
    tmf_vault_id_upper = tmf_vault_id.strip().upper()
    
    for doc in documents:
        # Skip the document being edited
        if exclude_id and doc.get('id') == exclude_id:
            continue
        
        # Compare TMF/Vault IDs (case-insensitive)
        if doc.get('tmf_vault_id', '').strip().upper() == tmf_vault_id_upper:
            duplicate_info = {
                'id': doc.get('id'),
                'trail': doc.get('trail', 'Unknown'),
                'document_name': doc.get('document_name', 'Unknown'),
                'created_by': doc.get('created_by', 'Unknown'),
                'created_at': doc.get('created_at', 'N/A'),
                'category': doc.get('category', 'Unknown'),
                'uat_round': doc.get('uat_round', 'N/A')
            }
            return True, duplicate_info
    
    return False, {}

def create_trail_document(data):
    """Create new trail document"""
    try:
        documents = load_data('trail_documents')
        
        # Generate unique ID
        document_id = str(uuid.uuid4())
        
        # Create document record
        document = {
            'id': document_id,
            'trail': data.get('trail', '').strip(),
            'category': data.get('category', 'Build'),
            'cr_number': data.get('cr_number', '').strip(),
            'te1': data.get('te1', '').strip(),
            'te2': data.get('te2', '').strip(),
            'document_name': data.get('document_name', '').strip(),
            'te_document': data.get('te_document', 'No'),
            'uat_round': data.get('uat_round', '').strip(),
            'tmf_vault_id': data.get('tmf_vault_id', '').strip(),
            'te1_approval_date': data.get('te1_approval_date'),
            'te2_approval_date': data.get('te2_approval_date'),
            'ctdm_approval_date': data.get('ctdm_approval_date'),
            'go_live_date': data.get('go_live_date'),
            'created_by': data.get('created_by', 'Unknown'),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': None,
            'updated_by': None
        }
        
        documents.append(document)
        
        if save_data('trail_documents', documents):
            # Log audit
            log_audit(
                username=data.get('created_by', 'Unknown'),
                action='create',
                category='trail_documents',
                entity_type='trail_document',
                entity_id=document_id,
                details={
                    'trail': document['trail'],
                    'category': document['category'],
                    'document_name': document['document_name'],
                    'tmf_vault_id': document['tmf_vault_id']
                }
            )
            return True, 'Trail document created successfully'
        
        return False, 'Failed to save trail document'
    
    except Exception as e:
        return False, f'Error creating trail document: {str(e)}'

def update_trail_document(document_id, data):
    """Update trail document"""
    try:
        documents = load_data('trail_documents')
        
        document = next((d for d in documents if d.get('id') == document_id), None)
        
        if not document:
            return False, 'Trail document not found'
        
        # Update fields
        document['trail'] = data.get('trail', '').strip()
        document['category'] = data.get('category', 'Build')
        document['cr_number'] = data.get('cr_number', '').strip()
        document['te1'] = data.get('te1', '').strip()
        document['te2'] = data.get('te2', '').strip()
        document['document_name'] = data.get('document_name', '').strip()
        document['te_document'] = data.get('te_document', 'No')
        document['uat_round'] = data.get('uat_round', '').strip()
        document['tmf_vault_id'] = data.get('tmf_vault_id', '').strip()
        document['te1_approval_date'] = data.get('te1_approval_date')
        document['te2_approval_date'] = data.get('te2_approval_date')
        document['ctdm_approval_date'] = data.get('ctdm_approval_date')
        document['go_live_date'] = data.get('go_live_date')
        document['updated_by'] = data.get('updated_by', 'Unknown')
        document['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if save_data('trail_documents', documents):
            # Log audit
            log_audit(
                username=data.get('updated_by', 'Unknown'),
                action='update',
                category='trail_documents',
                entity_type='trail_document',
                entity_id=document_id,
                details={
                    'trail': document['trail'],
                    'category': document['category'],
                    'document_name': document['document_name'],
                    'tmf_vault_id': document['tmf_vault_id']
                }
            )
            return True, 'Trail document updated successfully'
        
        return False, 'Failed to save trail document'
    
    except Exception as e:
        return False, f'Error updating trail document: {str(e)}'

def delete_trail_document(document_id):
    """Delete trail document"""
    try:
        documents = load_data('trail_documents')
        
        document = next((d for d in documents if d.get('id') == document_id), None)
        
        if not document:
            return False, 'Trail document not found'
        
        # Store info for audit log
        trail_info = {
            'trail': document.get('trail'),
            'category': document.get('category'),
            'document_name': document.get('document_name'),
            'tmf_vault_id': document.get('tmf_vault_id')
        }
        
        # Remove document
        documents = [d for d in documents if d.get('id') != document_id]
        
        if save_data('trail_documents', documents):
            # Log audit
            log_audit(
                username=document.get('created_by', 'Unknown'),
                action='delete',
                category='trail_documents',
                entity_type='trail_document',
                entity_id=document_id,
                details=trail_info
            )
            return True, 'Trail document deleted successfully'
        
        return False, 'Failed to delete trail document'
    
    except Exception as e:
        return False, f'Error deleting trail document: {str(e)}'