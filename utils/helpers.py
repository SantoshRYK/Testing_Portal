# utils/helpers.py
"""
Common helper utilities
"""
from datetime import datetime
from typing import List, Dict, Any
from config import STATUS_EMOJIS, STATUS_COLORS

def get_status_emoji(status: str) -> str:
    """Get emoji for status"""
    return STATUS_EMOJIS.get(status, "📝")

def get_status_color(status: str) -> str:
    """Get color for status"""
    return STATUS_COLORS.get(status, "gray")

def format_date(date_str: str, input_format: str = "%Y-%m-%d", output_format: str = "%d %b %Y") -> str:
    """Format date string"""
    try:
        dt = datetime.strptime(date_str, input_format)
        return dt.strftime(output_format)
    except:
        return date_str

def format_datetime(datetime_str: str, input_format: str = "%Y-%m-%d %H:%M:%S", output_format: str = "%d %b %Y %I:%M %p") -> str:
    """Format datetime string"""
    try:
        dt = datetime.strptime(datetime_str, input_format)
        return dt.strftime(output_format)
    except:
        return datetime_str

def filter_records_by_user(records: List[Dict], username: str) -> List[Dict]:
    """Filter records by username"""
    return [r for r in records if r.get('created_by') == username]

def filter_records_by_role(records: List[Dict], role: str, username: str) -> List[Dict]:
    """Filter records based on user role"""
    if role in ['superuser', 'admin', 'manager']:
        return records
    else:
        return filter_records_by_user(records, username)

def get_unique_values(records: List[Dict], field: str) -> List[str]:
    """Get unique values for a field from records"""
    values = set()
    for record in records:
        value = record.get(field)
        if value:
            values.add(value)
    return sorted(list(values))

def search_records(records: List[Dict], search_term: str, fields: List[str]) -> List[Dict]:
    """Search records across multiple fields"""
    if not search_term:
        return records
    
    search_term = search_term.lower()
    filtered = []
    
    for record in records:
        for field in fields:
            value = str(record.get(field, '')).lower()
            if search_term in value:
                filtered.append(record)
                break
    
    return filtered

def generate_id() -> str:
    """Generate unique ID based on timestamp"""
    return datetime.now().strftime("%Y%m%d%H%M%S%f")

def calculate_duration(start_date: str, end_date: str) -> int:
    """Calculate duration in days between two dates"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        return (end - start).days
    except:
        return 0
    
# utils/helpers.py
"""
Helper utility functions
"""
from datetime import datetime
import re

def get_status_emoji(status: str) -> str:
    """Get emoji for status/result"""
    status_emojis = {
        # UAT Status
        "Not Started": "⏳",
        "In Progress": "🔄",
        "Completed": "✅",
        "On Hold": "⏸️",
        "Cancelled": "❌",
        # UAT Results
        "Pending": "⏳",
        "Pass": "✅",
        "Fail": "❌",
        "Partial Pass": "⚠️",
        # Generic
        "Active": "🟢",
        "Inactive": "🔴",
        "Success": "✅",
        "Failed": "❌",
        "Warning": "⚠️"
    }
    return status_emojis.get(status, "📝")

def format_date(date_string: str, format_out: str = "%Y-%m-%d") -> str:
    """Format date string"""
    try:
        if date_string:
            date_obj = datetime.strptime(date_string, "%Y-%m-%d")
            return date_obj.strftime(format_out)
        return "N/A"
    except:
        return date_string

def format_datetime(datetime_string: str, format_out: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime string"""
    try:
        if datetime_string:
            dt_obj = datetime.strptime(datetime_string, "%Y-%m-%d %H:%M:%S")
            return dt_obj.strftime(format_out)
        return "N/A"
    except:
        return datetime_string

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to max length"""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe use"""
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    return filename

def calculate_duration(start_date: str, end_date: str) -> int:
    """Calculate duration in days between two dates"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        return (end - start).days
    except:
        return 0

def get_date_range_string(start_date: str, end_date: str) -> str:
    """Get formatted date range string"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").strftime("%b %d, %Y")
        end = datetime.strptime(end_date, "%Y-%m-%d").strftime("%b %d, %Y")
        return f"{start} - {end}"
    except:
        return f"{start_date} - {end_date}"

def is_date_in_past(date_string: str) -> bool:
    """Check if date is in the past"""
    try:
        date_obj = datetime.strptime(date_string, "%Y-%m-%d")
        return date_obj.date() < datetime.now().date()
    except:
        return False

def is_date_in_future(date_string: str) -> bool:
    """Check if date is in the future"""
    try:
        date_obj = datetime.strptime(date_string, "%Y-%m-%d")
        return date_obj.date() > datetime.now().date()
    except:
        return False

def get_relative_time(datetime_string: str) -> str:
    """Get relative time string (e.g., '2 hours ago')"""
    try:
        dt = datetime.strptime(datetime_string, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        diff = now - dt
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"
        else:
            return dt.strftime("%Y-%m-%d")
    except:
        return datetime_string

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_trial_id(trial_id: str) -> bool:
    """Validate trial ID format"""
    # Allow alphanumeric, hyphens, underscores
    pattern = r'^[a-zA-Z0-9\-_]+$'
    return re.match(pattern, trial_id) is not None

def get_system_emoji(system: str) -> str:
    """Get emoji for system"""
    system_emojis = {
        "INFORM": "📊",
        "VEEVA": "📁",
        "eCOA": "📱",
        "ePID": "🔬",
        "CGM": "📈",
        "Others": "📋"
    }
    return system_emojis.get(system, "📋")

def get_category_emoji(category: str) -> str:
    """Get emoji for category"""
    if "Build" in category:
        return "🏗️"
    elif "Change Request" in category:
        return "🔄"
    return "📝"

def get_therapeutic_area_emoji(area: str) -> str:
    """Get emoji for therapeutic area"""
    if "Diabetic" in area and "Obesity" not in area:
        return "💉"
    elif "Obesity" in area:
        return "⚖️"
    elif "CKAD" in area:
        return "🫀"
    elif "CagriSema" in area:
        return "💊"
    elif "Phase 1" in area or "NIS" in area:
        return "🔬"
    elif "Rare Disease" in area:
        return "🩺"
    return "🏥"