# utils/data_protection.py
"""
Simplified Data Protection Layer
NO circular dependencies - clean and safe
"""
import json
import hashlib
import os
from datetime import datetime
from typing import Any, Dict
from pathlib import Path


class DataProtection:
    """Handles data protection and integrity checks"""
    
    def __init__(self):
        """Initialize data protection"""
        self.is_enabled = True
        self.status_file = None  # We'll set this when config is loaded
    
    def calculate_checksum(self, data: Any) -> str:
        """Calculate MD5 checksum of data"""
        try:
            if isinstance(data, (dict, list)):
                data_str = json.dumps(data, sort_keys=True)
            else:
                data_str = str(data)
            return hashlib.md5(data_str.encode()).hexdigest()
        except:
            return ""
    
    def check_integrity(self, filename: str, data: Any) -> tuple[bool, str]:
        """
        Check data integrity (SIMPLIFIED - No logging to avoid loops)
        Returns: (is_valid, message)
        """
        # Basic validation - check if data is valid JSON structure
        if not isinstance(data, (dict, list)):
            return False, "Invalid data structure"
        
        return True, "OK"
    
    def verify_app_write(self) -> bool:
        """Verify that write operation is allowed"""
        # Always allow app writes
        return True
    
    def log_access_simple(self, operation: str, filename: str):
        """
        Simple logging without circular dependencies
        Writes directly to a separate log file
        """
        try:
            # Use separate protection log file (not audit_logs.json)
            log_dir = Path("data")
            log_file = log_dir / ".data_access.log"
            
            log_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {operation.upper()} | {filename}\n"
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except:
            pass  # Silently fail - don't break app


# Global protection instance
data_protection = DataProtection()