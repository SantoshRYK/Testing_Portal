# services/change_request_service.py
"""
Change Request business logic
"""
from typing import List, Dict, Optional
from utils.database import (
    load_change_requests, 
    add_change_request, 
    update_change_request,
    delete_change_request,
    get_change_request
)
from utils.auth import get_current_user, get_current_role
from services.audit_service import log_audit

def get_all_change_requests() -> List[Dict]:
    """Get all change requests"""
    return load_change_requests()

def get_user_change_requests(username: str) -> List[Dict]:
    """Get change requests for a specific user"""
    all_requests = load_change_requests()
    return [cr for cr in all_requests if cr.get('created_by') == username]

def get_filtered_change_requests(role: str, username: str) -> List[Dict]:
    """Get filtered change requests based on role"""
    all_requests = load_change_requests()
    
    if role in ['superuser', 'cdp', 'manager']:
        return all_requests
    else:
        return [cr for cr in all_requests if cr.get('created_by') == username]

def create_change_request(data: Dict) -> bool:
    """Create new change request"""
    try:
        data['created_by'] = get_current_user()
        success = add_change_request(data)
        
        if success:
            log_audit(
                username=get_current_user(),
                action="create",
                category="change_request",
                entity_type="change_request",
                entity_id=data.get('id', ''),
                details={
                    "trial_name": data.get('trial_name'),
                    "cr_no": data.get('cr_no'),
                    "category": data.get('category')
                }
            )
        
        return success
    except Exception as e:
        print(f"Error creating change request: {e}")
        return False

def update_change_request_record(cr_id: str, data: Dict) -> bool:
    """Update change request"""
    try:
        data['updated_by'] = get_current_user()
        success = update_change_request(cr_id, data)
        
        if success:
            log_audit(
                username=get_current_user(),
                action="update",
                category="change_request",
                entity_type="change_request",
                entity_id=cr_id,
                details={
                    "trial_name": data.get('trial_name'),
                    "cr_no": data.get('cr_no')
                }
            )
        
        return success
    except Exception as e:
        print(f"Error updating change request: {e}")
        return False

def delete_change_request_record(cr_id: str, cr_data: Dict) -> bool:
    """Delete change request"""
    try:
        success = delete_change_request(cr_id)
        
        if success:
            log_audit(
                username=get_current_user(),
                action="delete",
                category="change_request",
                entity_type="change_request",
                entity_id=cr_id,
                details={
                    "trial_name": cr_data.get('trial_name'),
                    "cr_no": cr_data.get('cr_no')
                }
            )
        
        return success
    except Exception as e:
        print(f"Error deleting change request: {e}")
        return False

def get_unique_values(field: str) -> List[str]:
    """Get unique values for a field"""
    requests = load_change_requests()
    values = set()
    
    for req in requests:
        value = req.get(field)
        if value:
            values.add(str(value))
    
    return sorted(list(values))

def search_change_requests(search_term: str, fields: List[str]) -> List[Dict]:
    """Search change requests"""
    if not search_term:
        return load_change_requests()
    
    requests = load_change_requests()
    search_term_lower = search_term.lower()
    filtered = []
    
    for req in requests:
        for field in fields:
            value = str(req.get(field, '')).lower()
            if search_term_lower in value:
                filtered.append(req)
                break
    
    return filtered