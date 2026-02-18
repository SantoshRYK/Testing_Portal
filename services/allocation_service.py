"""
Allocation Service - Flask Compatible
Handles all allocation-related business logic
"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# Data file path
DATA_DIR = Path(__file__).resolve().parents[1] / 'data'
ALLOCATIONS_FILE = DATA_DIR / 'allocations.json'


def _ensure_data_file():
    """Ensure data directory and allocations file exist"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not ALLOCATIONS_FILE.exists():
        with ALLOCATIONS_FILE.open('w', encoding='utf-8') as f:
            json.dump([], f, indent=4)


def _load_all_data() -> List[Dict]:
    """Load all data from file (including UAT records)"""
    try:
        _ensure_data_file()
        with ALLOCATIONS_FILE.open('r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading data: {e}")
        return []


def _load_allocations() -> List[Dict]:
    """Load only allocation records from file"""
    all_data = _load_all_data()
    return [item for item in all_data if item.get('record_type') != 'uat']


def _save_all_data(data: List[Dict]) -> bool:
    """Save all data to file"""
    try:
        _ensure_data_file()
        with ALLOCATIONS_FILE.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving data: {e}")
        return False


def _save_allocations(allocations: List[Dict]) -> bool:
    """Save allocations while preserving UAT records"""
    try:
        all_data = _load_all_data()
        uat_records = [item for item in all_data if item.get('record_type') == 'uat']
        combined_data = uat_records + allocations
        return _save_all_data(combined_data)
    except Exception as e:
        print(f"Error saving allocations: {e}")
        return False


def get_all_allocations() -> List[Dict]:
    """Get all allocation records"""
    return _load_allocations()


def get_allocation_by_id(allocation_id: str) -> Optional[Dict]:
    """Get allocation by ID"""
    allocations = _load_allocations()
    for allocation in allocations:
        if allocation.get('id') == allocation_id:
            return allocation
    return None


def get_allocations_by_user(username: str) -> List[Dict]:
    """Get allocations created by specific user"""
    allocations = _load_allocations()
    return [a for a in allocations if a.get('created_by') == username]


def get_allocations_by_engineer(engineer_name: str) -> List[Dict]:
    """Get allocations for specific engineer"""
    allocations = _load_allocations()
    return [a for a in allocations if a.get('test_engineer_name') == engineer_name]


def get_allocations_by_role(role: str, username: str) -> List[Dict]:
    """Get allocations based on user role"""
    if role in ['admin', 'manager', 'superuser']:
        return get_all_allocations()
    else:
        return get_allocations_by_user(username)


def create_allocation_record(allocation_data: Dict, username: str) -> Tuple[bool, str]:
    """Create new allocation record"""
    try:
        # Generate ID
        allocation_data['id'] = datetime.now().strftime("%Y%m%d%H%M%S")
        allocation_data['created_by'] = username
        allocation_data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        allocation_data['record_type'] = 'allocation'
        
        # Load existing allocations
        allocations = _load_allocations()
        
        # Add new allocation
        allocations.append(allocation_data)
        
        # Save
        if _save_allocations(allocations):
            return True, "Allocation created successfully"
        else:
            return False, "Failed to save allocation"
    
    except Exception as e:
        return False, f"Error creating allocation: {str(e)}"


def update_allocation_record(allocation_id: str, updated_data: Dict, username: str) -> Tuple[bool, str]:
    """Update existing allocation record"""
    try:
        allocations = _load_allocations()
        
        # Find and update allocation
        found = False
        for i, allocation in enumerate(allocations):
            if allocation.get('id') == allocation_id:
                # Update fields
                allocations[i].update(updated_data)
                allocations[i]['updated_by'] = username
                allocations[i]['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                found = True
                break
        
        if not found:
            return False, "Allocation not found"
        
        # Save
        if _save_allocations(allocations):
            return True, "Allocation updated successfully"
        else:
            return False, "Failed to save allocation"
    
    except Exception as e:
        return False, f"Error updating allocation: {str(e)}"


def delete_allocation_record(allocation_id: str) -> Tuple[bool, str]:
    """Delete allocation record"""
    try:
        allocations = _load_allocations()
        
        # Filter out the allocation to delete
        original_count = len(allocations)
        allocations = [a for a in allocations if a.get('id') != allocation_id]
        
        if len(allocations) == original_count:
            return False, "Allocation not found"
        
        # Save
        if _save_allocations(allocations):
            return True, "Allocation deleted successfully"
        else:
            return False, "Failed to delete allocation"
    
    except Exception as e:
        return False, f"Error deleting allocation: {str(e)}"


def get_allocation_statistics() -> Dict:
    """Get allocation statistics for dashboard"""
    allocations = _load_allocations()
    
    stats = {
        'total': len(allocations),
        'by_system': {},
        'by_category': {},
        'by_therapeutic_area': {},
        'by_engineer': {},
        'by_role': {},
        'by_creator': {}
    }
    
    for allocation in allocations:
        # Count by system
        system = allocation.get('system', 'Unknown')
        stats['by_system'][system] = stats['by_system'].get(system, 0) + 1
        
        # Count by category
        category_type = allocation.get('trial_category_type', 'Unknown')
        if not category_type:
            category = allocation.get('trial_category', 'Unknown')
            category_type = 'Change Request' if 'Change Request' in category else 'Build'
        stats['by_category'][category_type] = stats['by_category'].get(category_type, 0) + 1
        
        # Count by therapeutic area
        area_type = allocation.get('therapeutic_area_type', '')
        if not area_type:
            area = allocation.get('therapeutic_area', 'Unknown')
            area_type = 'Others' if 'Others -' in area else area
        stats['by_therapeutic_area'][area_type] = stats['by_therapeutic_area'].get(area_type, 0) + 1
        
        # Count by engineer
        engineer = allocation.get('test_engineer_name', 'Unknown')
        stats['by_engineer'][engineer] = stats['by_engineer'].get(engineer, 0) + 1
        
        # Count by role
        role = allocation.get('role', 'Unknown')
        stats['by_role'][role] = stats['by_role'].get(role, 0) + 1
        
        # Count by creator
        creator = allocation.get('created_by', 'Unknown')
        stats['by_creator'][creator] = stats['by_creator'].get(creator, 0) + 1
    
    return stats


def calculate_engineer_efficiency(allocations: List[Dict]) -> List[Dict]:
    """Calculate efficiency metrics for each engineer"""
    engineer_metrics = {}
    
    for allocation in allocations:
        engineer = allocation.get('test_engineer_name', 'Unknown')
        
        if engineer not in engineer_metrics:
            engineer_metrics[engineer] = {
                'name': engineer,
                'total_allocations': 0,
                'total_trials': set(),
                'total_days': 0,
                'systems': set(),
                'categories': {'Build': 0, 'Change Request': 0}
            }
        
        # Count allocations
        engineer_metrics[engineer]['total_allocations'] += 1
        
        # Count unique trials
        trial_id = allocation.get('trial_id')
        if trial_id:
            engineer_metrics[engineer]['total_trials'].add(trial_id)
        
        # Calculate duration
        try:
            start_date = datetime.strptime(allocation.get('start_date', '2024-01-01'), '%Y-%m-%d')
            end_date = datetime.strptime(allocation.get('end_date', '2024-12-31'), '%Y-%m-%d')
            duration = (end_date - start_date).days
            engineer_metrics[engineer]['total_days'] += duration
        except:
            pass
        
        # Count systems
        system = allocation.get('system')
        if system:
            engineer_metrics[engineer]['systems'].add(system)
        
        # Count categories
        category_type = allocation.get('trial_category_type', 'Build')
        if not category_type:
            category = allocation.get('trial_category', 'Build')
            category_type = 'Change Request' if 'Change Request' in category else 'Build'
        
        engineer_metrics[engineer]['categories'][category_type] += 1
    
    # Convert to list and calculate efficiency score
    result = []
    for engineer, metrics in engineer_metrics.items():
        result.append({
            'engineer': engineer,
            'total_allocations': metrics['total_allocations'],
            'unique_trials': len(metrics['total_trials']),
            'total_days': metrics['total_days'],
            'unique_systems': len(metrics['systems']),
            'build_count': metrics['categories']['Build'],
            'change_request_count': metrics['categories']['Change Request'],
            'avg_days_per_allocation': round(metrics['total_days'] / metrics['total_allocations'], 1) if metrics['total_allocations'] > 0 else 0,
            'efficiency_score': round((metrics['total_allocations'] * len(metrics['total_trials'])) / max(metrics['total_days'], 1) * 100, 2)
        })
    
    return sorted(result, key=lambda x: x['efficiency_score'], reverse=True)


def search_allocations(filters: Dict) -> List[Dict]:
    """Search allocations with filters"""
    allocations = _load_allocations()
    
    # Apply filters
    if filters.get('system') and filters['system'] != 'All':
        allocations = [a for a in allocations if a.get('system') == filters['system']]
    
    if filters.get('category') and filters['category'] != 'All':
        if filters['category'] == 'Build':
            allocations = [a for a in allocations 
                          if a.get('trial_category_type') == 'Build' or a.get('trial_category') == 'Build']
        elif filters['category'] == 'Change Request':
            allocations = [a for a in allocations 
                          if a.get('trial_category_type') == 'Change Request' or 'Change Request' in a.get('trial_category', '')]
    
    if filters.get('therapeutic_area') and filters['therapeutic_area'] != 'All':
        area_filter = filters['therapeutic_area']
        if area_filter == 'Others':
            allocations = [a for a in allocations 
                          if a.get('therapeutic_area_type') == 'Others' or 'Others -' in a.get('therapeutic_area', '')]
        else:
            allocations = [a for a in allocations 
                          if a.get('therapeutic_area_type') == area_filter or area_filter in a.get('therapeutic_area', '')]
    
    if filters.get('engineer') and filters['engineer'] != 'All':
        allocations = [a for a in allocations if a.get('test_engineer_name') == filters['engineer']]
    
    if filters.get('role') and filters['role'] != 'All':
        allocations = [a for a in allocations if a.get('role') == filters['role']]
    
    if filters.get('trial_id') and filters['trial_id'] != 'All':
        allocations = [a for a in allocations if a.get('trial_id') == filters['trial_id']]
    
    if filters.get('created_by') and filters['created_by'] != 'All':
        allocations = [a for a in allocations if a.get('created_by') == filters['created_by']]
    
    # Date filters
    if filters.get('start_date'):
        try:
            allocations = [a for a in allocations 
                          if datetime.strptime(a.get('start_date', '2024-01-01'), '%Y-%m-%d').date() >= filters['start_date']]
        except:
            pass
    
    if filters.get('end_date'):
        try:
            allocations = [a for a in allocations 
                          if datetime.strptime(a.get('end_date', '2024-12-31'), '%Y-%m-%d').date() <= filters['end_date']]
        except:
            pass
    
    return allocations


def list_allocations() -> List[Dict]:
    """List all allocations (alias for compatibility)"""
    return get_all_allocations()