# scripts/lock_data.py
"""
Lock Data Files (Superuser Only)
Enables maximum protection - only app can write
"""
import sys
from pathlib import Path
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config import PROTECTION_STATUS_FILE


def lock_data():
    """Enable data protection lock"""
    print("🔒 Locking Data Files")
    print("=" * 70)
    
    # Verify superuser
    print("\n⚠️ This operation requires superuser privileges")
    username = input("Enter superuser username: ")
    password = input("Enter superuser password: ")
    
    # Simple verification (you can enhance this)
    if username != "superuser":
        print("❌ Only superuser can lock data!")
        return 1
    
    try:
        # Create lock status
        status = {
            "protection_enabled": True,
            "locked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "locked_by": username,
            "lock_level": "maximum",
            "allow_app_writes": True,
            "allow_manual_edits": False,
            "checksums": {}
        }
        
        with open(PROTECTION_STATUS_FILE, 'w') as f:
            json.dump(status, f, indent=4)
        
        print("\n✅ Data protection ENABLED")
        print("   🔒 Manual editing: BLOCKED")
        print("   ✅ App writes: ALLOWED")
        print(f"   👤 Locked by: {username}")
        print(f"   📅 Locked at: {status['locked_at']}")
        
        return 0
    
    except Exception as e:
        print(f"\n❌ Failed to lock data: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(lock_data())