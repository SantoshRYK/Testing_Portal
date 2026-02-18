"""
Quality Service - Flask Compatible
Handles business logic for quality records with auto-requirement round tracking
"""
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Tuple

# Data file paths
DATA_DIR = Path(__file__).resolve().parents[1] / 'data'
QUALITY_FILE = DATA_DIR / 'quality_records.json'

def _ensure_data_file():
    """Ensure data directory and file exist"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not QUALITY_FILE.exists():
        QUALITY_FILE.write_text("[]", encoding="utf-8")

def _load_records() -> List[Dict]:
    """Load all quality records"""
    try:
        _ensure_data_file()
        with QUALITY_FILE.open('r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading quality records: {e}")
        return []

def _save_records(records: List[Dict]) -> bool:
    """Save quality records to file"""
    try:
        with QUALITY_FILE.open('w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving quality records: {e}")
        return False

def generate_record_id() -> str:
    """Generate unique record ID"""
    records = _load_records()
    if not records:
        return "QM001"
    
    try:
        last_id = max([int(r['record_id'][2:]) for r in records if r.get('record_id', '').startswith('QM')])
        return f"QM{str(last_id + 1).zfill(3)}"
    except (ValueError, KeyError):
        return f"QM{len(records) + 1:03d}"

def calculate_defect_density(total_requirements: int, total_failures: int) -> float:
    """Calculate defect density percentage"""
    if total_requirements == 0:
        return 0.0
    return round((total_failures / total_requirements) * 100, 2)

def get_requirement_round(trial_id: str, requirement_type: str, wizard_records: Optional[List[Dict]] = None) -> int:
    """
    Calculate requirement-specific round number (auto-incrementing per requirement type)
    
    Args:
        trial_id: Trial identifier
        requirement_type: Type of requirement (Forms, Editchecks, etc.)
        wizard_records: Current wizard records (for session-based calculation)
    
    Returns:
        int: Next requirement round number for this type (starts from 1)
    """
    # Load all existing records for this trial
    all_records = _load_records()
    trial_records = [r for r in all_records if r.get('trial_id') == trial_id 
                     and r.get('type_of_requirement') == requirement_type]
    
    # Include wizard records if provided
    if wizard_records:
        wizard_type_records = [r for r in wizard_records if r.get('type_of_requirement') == requirement_type]
        trial_records.extend(wizard_type_records)
    
    # Get max requirement round for this type
    if not trial_records:
        return 1
    
    max_req_round = max([r.get('requirement_round', 0) for r in trial_records])
    return max_req_round + 1

def create_record(record_data: dict, username: str) -> Tuple[bool, str]:
    """Create new quality record with auto requirement round"""
    try:
        records = _load_records()
        
        # Add metadata
        record = record_data.copy()
        record['record_id'] = generate_record_id()
        record['created_by'] = username
        record['created_at'] = datetime.utcnow().isoformat()
        record['updated_at'] = datetime.utcnow().isoformat()
        record['status'] = 'Active'
        
        # Ensure requirement_round exists (calculate if not present)
        if 'requirement_round' not in record or record.get('requirement_round') == 0:
            record['requirement_round'] = get_requirement_round(
                record.get('trial_id', ''),
                record.get('type_of_requirement', '')
            )
        
        # Calculate defect density
        record['defect_density'] = calculate_defect_density(
            int(record.get('total_requirements', 0)),
            int(record.get('total_failures', 0))
        )
        
        # Convert numeric fields
        numeric_fields = ['no_of_rounds', 'current_round', 'requirement_round', 
                         'total_requirements', 'total_failures',
                         'spec_issue', 'mock_crf_issue', 'programming_issue', 'scripting_issue']
        for field in numeric_fields:
            if field in record:
                try:
                    record[field] = int(record[field])
                except:
                    if field == 'requirement_round':
                        record[field] = 1
                    else:
                        record[field] = 0
        
        # Validation
        if int(record.get('total_failures', 0)) > int(record.get('total_requirements', 0)):
            return False, "Total failures cannot exceed total requirements"
        
        failure_sum = (record.get('spec_issue', 0) + record.get('mock_crf_issue', 0) + 
                      record.get('programming_issue', 0) + record.get('scripting_issue', 0))
        if failure_sum > record.get('total_failures', 0):
            return False, f"Sum of failure reasons ({failure_sum}) cannot exceed total failures"
        
        records.append(record)
        
        if _save_records(records):
            return True, f"Quality record {record['record_id']} created successfully"
        return False, "Failed to save record"
        
    except Exception as e:
        return False, f"Error creating record: {e}"

def get_all_records() -> List[Dict]:
    """Get all quality records"""
    return _load_records()

def get_record_by_id(record_id: str) -> Optional[Dict]:
    """Get record by ID"""
    records = _load_records()
    for record in records:
        if record.get('record_id') == record_id:
            return record
    return None

def get_records_by_user(username: str) -> List[Dict]:
    """Get records created by user"""
    records = _load_records()
    return [r for r in records if r.get('created_by') == username]

def get_records_by_trial(trial_id: str) -> List[Dict]:
    """Get records for specific trial"""
    records = _load_records()
    return [r for r in records if r.get('trial_id') == trial_id]

def get_records_by_trial_and_type(trial_id: str, requirement_type: str) -> List[Dict]:
    """Get records for specific trial and requirement type"""
    records = _load_records()
    return [r for r in records if r.get('trial_id') == trial_id 
            and r.get('type_of_requirement') == requirement_type]

def update_record(record_id: str, updates: dict, username: str) -> Tuple[bool, str]:
    """Update quality record"""
    try:
        records = _load_records()
        
        for i, record in enumerate(records):
            if record.get('record_id') == record_id:
                # Update fields
                record.update(updates)
                record['updated_at'] = datetime.utcnow().isoformat()
                record['updated_by'] = username
                
                # Recalculate defect density
                record['defect_density'] = calculate_defect_density(
                    int(record.get('total_requirements', 0)),
                    int(record.get('total_failures', 0))
                )
                
                records[i] = record
                
                if _save_records(records):
                    return True, f"Record {record_id} updated successfully"
                return False, "Failed to save record"
        
        return False, f"Record {record_id} not found"
        
    except Exception as e:
        return False, f"Error updating record: {e}"

def delete_record(record_id: str, username: str) -> Tuple[bool, str]:
    """Delete quality record"""
    try:
        records = _load_records()
        original_count = len(records)
        
        records = [r for r in records if r.get('record_id') != record_id]
        
        if len(records) == original_count:
            return False, f"Record {record_id} not found"
        
        if _save_records(records):
            return True, f"Record {record_id} deleted successfully"
        return False, "Failed to delete record"
        
    except Exception as e:
        return False, f"Error deleting record: {e}"

def get_unique_values(field: str) -> List[str]:
    """Get unique values for a field (for filters)"""
    records = _load_records()
    values = set(str(r.get(field)) for r in records if field in r and r.get(field) is not None)
    return sorted(list(values))

def get_statistics(filters: Optional[Dict] = None) -> Dict:
    """Get statistics for dashboard with proper cumulative calculations"""
    all_records = _load_records()
    
    # Apply filters
    filtered_records = all_records
    if filters:
        for key, value in filters.items():
            if value and value != "All":
                filtered_records = [r for r in filtered_records if str(r.get(key)) == str(value)]
    
    if not filtered_records:
        return {
            'total_records': 0,
            'unique_trials': 0,
            'total_requirements': 0,
            'total_failures': 0,
            'avg_defect_density': 0.0,
            'failure_reasons': {},
            'type_breakdown': {},
            'phase_breakdown': {},
            'round_breakdown': {},
            'requirement_round_breakdown': {}
        }
    
    # Group by trial
    trials_data = {}
    for record in filtered_records:
        trial_id = record.get('trial_id')
        if trial_id not in trials_data:
            trials_data[trial_id] = []
        trials_data[trial_id].append(record)
    
    # Sort each trial by round
    for trial_id in trials_data:
        trials_data[trial_id].sort(key=lambda x: x.get('current_round', 0))
    
    # Calculate cumulative totals
    total_requirements = 0
    total_failures = 0
    latest_records = []
    
    for trial_id, records in trials_data.items():
        trial_req = 0
        trial_fail = 0
        prev_failures = 0
        
        for i, record in enumerate(records):
            curr_req = record.get('total_requirements', 0)
            curr_fail = record.get('total_failures', 0)
            
            if i == 0:
                trial_req = curr_req
                trial_fail = curr_fail
            else:
                new_additions = curr_req - prev_failures
                if new_additions > 0:
                    trial_req += new_additions
                trial_fail += curr_fail
            
            prev_failures = curr_fail
        
        total_requirements += trial_req
        total_failures += trial_fail
        latest_records.append(records[-1])
    
    # Calculate average defect density
    avg_defect_density = sum(r.get('defect_density', 0) for r in latest_records) / len(latest_records) if latest_records else 0
    
    # Failure reasons (cumulative)
    failure_reasons = {
        'Spec Issue': sum(r.get('spec_issue', 0) for r in filtered_records),
        'Mock CRF Issue': sum(r.get('mock_crf_issue', 0) for r in filtered_records),
        'Programming Issue': sum(r.get('programming_issue', 0) for r in filtered_records),
        'Scripting Issue': sum(r.get('scripting_issue', 0) for r in filtered_records)
    }
    
    # Breakdowns
    type_breakdown = {}
    phase_breakdown = {}
    round_breakdown = {}
    requirement_round_breakdown = {}
    
    for record in filtered_records:
        req_type = record.get('type_of_requirement', 'Unknown')
        type_breakdown[req_type] = type_breakdown.get(req_type, 0) + 1
        
        phase = record.get('phase', 'Unknown')
        phase_breakdown[phase] = phase_breakdown.get(phase, 0) + 1
        
        round_num = f"Round {record.get('current_round', 0)}"
        round_breakdown[round_num] = round_breakdown.get(round_num, 0) + 1
        
        req_round = f"{req_type} R{record.get('requirement_round', 0)}"
        requirement_round_breakdown[req_round] = requirement_round_breakdown.get(req_round, 0) + 1
    
    return {
        'total_records': len(filtered_records),
        'unique_trials': len(trials_data),
        'total_requirements': total_requirements,
        'total_failures': total_failures,
        'avg_defect_density': round(avg_defect_density, 2),
        'failure_reasons': failure_reasons,
        'type_breakdown': type_breakdown,
        'phase_breakdown': phase_breakdown,
        'round_breakdown': round_breakdown,
        'requirement_round_breakdown': requirement_round_breakdown
    }

# Class-based API for backward compatibility
class QualityService:
    """Service class for quality operations"""
    
    def __init__(self):
        _ensure_data_file()
    
    def generate_record_id(self):
        return generate_record_id()
    
    def get_requirement_round(self, trial_id: str, requirement_type: str, wizard_records: Optional[List[Dict]] = None):
        return get_requirement_round(trial_id, requirement_type, wizard_records)
    
    def create_record(self, record_data: dict, username: str):
        success, message = create_record(record_data, username)
        return success, message, None
    
    def get_all_records(self):
        return get_all_records()
    
    def get_record_by_id(self, record_id: str):
        return get_record_by_id(record_id)
    
    def get_records_by_user(self, username: str):
        return get_records_by_user(username)
    
    def get_records_by_trial(self, trial_id: str):
        return get_records_by_trial(trial_id)
    
    def get_records_by_trial_and_type(self, trial_id: str, requirement_type: str):
        return get_records_by_trial_and_type(trial_id, requirement_type)
    
    def update_record(self, record_id: str, updates: dict, username: str):
        return update_record(record_id, updates, username)
    
    def delete_record(self, record_id: str, username: str):
        return delete_record(record_id, username)
    
    def get_unique_values(self, field: str):
        return get_unique_values(field)
    
    def get_statistics(self, filters: Optional[Dict] = None):
        return get_statistics(filters)