"""
UAT Service - Business logic for UAT records
Flask version - Converted from Streamlit
"""
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import json
import os
from config import UAT_RECORDS_FILE, AUDIT_LOGS_FILE

def _load_uat_records() -> List[Dict]:
    """Load UAT records from JSON file"""
    try:
        if os.path.exists(UAT_RECORDS_FILE):
            with open(UAT_RECORDS_FILE, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading UAT records: {e}")
        return []

def _save_uat_records(records: List[Dict]) -> bool:
    """Save UAT records to JSON file"""
    try:
        with open(UAT_RECORDS_FILE, 'w') as f:
            json.dump(records, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving UAT records: {e}")
        return False

def create_uat_record(uat_data: Dict, username: str) -> Tuple[bool, str]:
    """Create new UAT record"""
    try:
        # Validate required fields
        required_fields = ['trial_id', 'uat_round', 'category', 'planned_start_date', 
                          'planned_end_date', 'status', 'result']
        
        for field in required_fields:
            if not uat_data.get(field):
                return False, f"{field.replace('_', ' ').title()} is required"
        
        # Check for date difference and require comment
        planned_start = uat_data.get('planned_start_date')
        planned_end = uat_data.get('planned_end_date')
        actual_start = uat_data.get('actual_start_date')
        actual_end = uat_data.get('actual_end_date')
        
        has_date_difference = False
        if actual_start and actual_start != planned_start:
            has_date_difference = True
        if actual_end and actual_end != planned_end:
            has_date_difference = True
        
        if has_date_difference and not uat_data.get('date_difference_reason'):
            return False, "Reason for date difference is required when actual dates differ from planned dates"
        
        # Load existing records
        records = _load_uat_records()
        
        # Create new record
        record = {
            'id': datetime.now().strftime("%Y%m%d%H%M%S"),
            'trial_id': uat_data['trial_id'].strip(),
            'uat_round': uat_data['uat_round'].strip(),
            'category': uat_data['category'].strip(),
            'category_type': uat_data.get('category_type', 'Build'),
            'planned_start_date': planned_start,
            'planned_end_date': planned_end,
            'actual_start_date': actual_start or None,
            'actual_end_date': actual_end or None,
            'date_difference_reason': uat_data.get('date_difference_reason', '').strip() if has_date_difference else None,
            'status': uat_data['status'],
            'result': uat_data['result'],
            'email_body': uat_data.get('email_body', '').strip(),
            'created_by': username,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'record_type': 'uat'
        }
        
        records.append(record)
        
        if _save_uat_records(records):
            return True, "UAT record created successfully"
        return False, "Failed to save UAT record"
        
    except Exception as e:
        return False, f"Error creating UAT record: {str(e)}"

def get_uat_records_by_role(role: str, username: str) -> List[Dict]:
    """Get UAT records based on user role"""
    records = _load_uat_records()
    
    if role in ['superuser', 'admin', 'manager']:
        return records
    else:
        return [r for r in records if r.get('created_by') == username]

def get_uat_record_by_id(record_id: str) -> Optional[Dict]:
    """Get single UAT record by ID"""
    records = _load_uat_records()
    for record in records:
        if record.get('id') == record_id:
            return record
    return None

def update_uat_record(record_id: str, uat_data: Dict, username: str) -> Tuple[bool, str]:
    """Update UAT record"""
    try:
        records = _load_uat_records()
        
        # Check for date difference and require comment
        planned_start = uat_data.get('planned_start_date')
        planned_end = uat_data.get('planned_end_date')
        actual_start = uat_data.get('actual_start_date')
        actual_end = uat_data.get('actual_end_date')
        
        has_date_difference = False
        if actual_start and actual_start != planned_start:
            has_date_difference = True
        if actual_end and actual_end != planned_end:
            has_date_difference = True
        
        if has_date_difference and not uat_data.get('date_difference_reason'):
            return False, "Reason for date difference is required when actual dates differ from planned dates"
        
        for i, record in enumerate(records):
            if record.get('id') == record_id:
                # Update fields
                records[i].update({
                    'trial_id': uat_data['trial_id'].strip(),
                    'uat_round': uat_data['uat_round'].strip(),
                    'category': uat_data['category'].strip(),
                    'category_type': uat_data.get('category_type', 'Build'),
                    'planned_start_date': planned_start,
                    'planned_end_date': planned_end,
                    'actual_start_date': actual_start or None,
                    'actual_end_date': actual_end or None,
                    'date_difference_reason': uat_data.get('date_difference_reason', '').strip() if has_date_difference else None,
                    'status': uat_data['status'],
                    'result': uat_data['result'],
                    'email_body': uat_data.get('email_body', '').strip(),
                    'updated_by': username,
                    'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                if _save_uat_records(records):
                    return True, "UAT record updated successfully"
                return False, "Failed to save changes"
        
        return False, "UAT record not found"
        
    except Exception as e:
        return False, f"Error updating UAT record: {str(e)}"

def delete_uat_record(record_id: str) -> Tuple[bool, str]:
    """Delete UAT record"""
    try:
        records = _load_uat_records()
        original_count = len(records)
        
        records = [r for r in records if r.get('id') != record_id]
        
        if len(records) < original_count:
            if _save_uat_records(records):
                return True, "UAT record deleted successfully"
            return False, "Failed to delete UAT record"
        
        return False, "UAT record not found"
        
    except Exception as e:
        return False, f"Error deleting UAT record: {str(e)}"

def get_uat_statistics(records: List[Dict]) -> Dict:
    """Calculate UAT statistics"""
    stats = {
        'total': len(records),
        'by_status': {},
        'by_result': {},
        'by_category': {},
        'completed': 0,
        'in_progress': 0,
        'passed': 0,
        'failed': 0,
        'pending': 0
    }
    
    for record in records:
        status = record.get('status', 'Unknown')
        result = record.get('result', 'Unknown')
        category = record.get('category_type', 'Unknown')
        
        stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
        stats['by_result'][result] = stats['by_result'].get(result, 0) + 1
        stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
        
        if status == 'Completed':
            stats['completed'] += 1
        elif status == 'In Progress':
            stats['in_progress'] += 1
        
        if result == 'Pass':
            stats['passed'] += 1
        elif result == 'Fail':
            stats['failed'] += 1
        elif result == 'Pending':
            stats['pending'] += 1
    
    return stats

def get_trial_ids() -> List[str]:
    """Get unique trial IDs"""
    records = _load_uat_records()
    trial_ids = []
    for r in records:
        trial_id = r.get('trial_id')
        if trial_id and trial_id not in trial_ids:
            trial_ids.append(trial_id)
    return sorted(trial_ids)