# scripts/check_data_protection.py
"""
Check Data Protection Status
Shows current protection status and integrity checks
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
    """Check data protection status"""
    print("🔒 Data Protection Status Check")
    print("=" * 70)
    
    # Get protection status
    status = data_protection.get_protection_status()
    
    print("\n📊 Protection Status:")
    print(f"   Protection Enabled: {'✅ Yes' if status.get('protection_enabled') else '❌ No'}")
    print(f"   Initialized At: {status.get('initialized_at', 'N/A')}")
    print(f"   Last Check: {status.get('last_check', 'N/A')}")
    print(f"   Locked By: {status.get('locked_by', 'N/A')}")
    print(f"   Locked At: {status.get('locked_at', 'N/A')}")
    
    # Check each data file
    print("\n📁 Data Files Status:")
    print("-" * 70)
    
    data_files = BACKUP_CONFIG["include_files"]
    
    for filename in data_files:
        filepath = os.path.join(DATA_DIR, filename)
        
        if os.path.exists(filepath):
            # Load file
            data = load_json(filepath, default=[])
            
            # Check integrity
            is_valid, message = data_protection.check_integrity(filename, data)
            
            # Get checksum
            current_checksum = data_protection.calculate_checksum(data)
            stored_checksum = status.get('checksums', {}).get(filename, 'N/A')
            
            # Get file size
            file_size = os.path.getsize(filepath)
            size_kb = file_size / 1024
            
            # Count records
            if isinstance(data, list):
                record_count = len(data)
            elif isinstance(data, dict):
                record_count = len(data)
            else:
                record_count = 0
            
            status_icon = "✅" if is_valid else "⚠️"
            
            print(f"\n{status_icon} {filename}")
            print(f"   Records: {record_count}")
            print(f"   Size: {size_kb:.2f} KB")
            print(f"   Checksum: {current_checksum[:16]}...")
            print(f"   Integrity: {message}")
            
            if not is_valid:
                print(f"   ⚠️ WARNING: {message}")
        else:
            print(f"\n❌ {filename}")
            print(f"   Status: File not found")
    
    print("\n" + "=" * 70)
    print("✅ Protection check completed")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())