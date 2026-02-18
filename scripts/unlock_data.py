# scripts/unlock_data.py
"""
Unlock Data Files (Superuser Only)
Temporarily disables protection for maintenance
"""
import sys
from pathlib import Path
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config import PROTECTION_STATUS_FILE


def unlock_data():
    """Disable data protection lock"""
    print("🔓 Unlocking Data Files")
    print("=" * 70)
    print("\n⚠️ WARNING: This will allow manual editing of data files!")
    print("   Only use for maintenance purposes.")
    print("   Remember to lock again after maintenance!")
    
    # Verify superuser
    print("\n🔐 Superuser verification required")
    username = input("Enter superuser username: ")
    password = input("Enter superuser password: ")
    
    if username != "superuser":
        print("❌ Only superuser can unlock data!")
        return 1
    
    confirm = input("\nType 'UNLOCK' to confirm: ")
    if confirm != 'UNLOCK':
        print("❌ Unlock cancelled")
        return 0
    
    try:
        # Read current status
        if Path(PROTECTION_STATUS_FILE).exists():
            with open(PROTECTION_STATUS_FILE, 'r') as f:
                status = json.load(f)
        else:
            status = {}
        
        # Update status
        status.update({
            "protection_enabled": False,
            "unlocked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "unlocked_by": username,
            "unlock_reason": "manual_maintenance"
        })
        
        with open(PROTECTION_STATUS_FILE, 'w') as f:
            json.dump(status, f, indent=4)
        
        print("\n✅ Data protection DISABLED")
        print("   🔓 Manual editing: ALLOWED")
        print("   ⚠️ Data is vulnerable to accidental changes!")
        print(f"   👤 Unlocked by: {username}")
        print(f"   📅 Unlocked at: {status['unlocked_at']}")
        print("\n💡 Remember to lock again after maintenance:")
        print("   python scripts/lock_data.py")
        
        return 0
    
    except Exception as e:
        print(f"\n❌ Failed to unlock data: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(unlock_data())