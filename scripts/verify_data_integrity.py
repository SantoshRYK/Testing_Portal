# scripts/verify_data_integrity.py
"""
Verify Data Integrity
Checks all data files for tampering or corruption
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.data_protection import data_protection
from utils.database import load_json
from config import DATA_DIR, BACKUP_CONFIG
import os


def main():
    """Verify data integrity"""
    print("🔍 Data Integrity Verification")
    print("=" * 70)
    
    data_files = BACKUP_CONFIG["include_files"]
    
    issues_found = 0
    files_checked = 0
    
    for filename in data_files:
        filepath = os.path.join(DATA_DIR, filename)
        
        if not os.path.exists(filepath):
            print(f"\n⚠️ {filename} - File not found")
            continue
        
        files_checked += 1
        
        # Load data
        data = load_json(filepath, default=[])
        
        # Check integrity
        is_valid, message = data_protection.check_integrity(filename, data)
        
        if is_valid:
            print(f"\n✅ {filename}")
            print(f"   Status: OK")
            print(f"   Records: {len(data) if isinstance(data, (list, dict)) else 'N/A'}")
        else:
            print(f"\n❌ {filename}")
            print(f"   Status: INTEGRITY ISSUE")
            print(f"   Issue: {message}")
            issues_found += 1
    
    print("\n" + "=" * 70)
    print(f"📊 Verification Summary:")
    print(f"   Files checked: {files_checked}")
    print(f"   Issues found: {issues_found}")
    
    if issues_found == 0:
        print("\n✅ All data files passed integrity check!")
        return 0
    else:
        print(f"\n⚠️ {issues_found} file(s) have integrity issues!")
        print("   Consider restoring from backup if data is corrupted.")
        return 1


if __name__ == "__main__":
    sys.exit(main())